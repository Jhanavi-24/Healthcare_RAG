# retrieval/retriever.py

from openai import OpenAI
from embeddings.embedder import Embedder
from embeddings.pinecone_store import PineconeStore
from retrieval.confidence import score_chunk, answer_confidence, confidence_label
from config.settings import settings

SYSTEM_PROMPT = """You are a clinical knowledge assistant for healthcare professionals.

Your rules:
1. Answer ONLY using the provided context — never use outside knowledge
2. Cite every fact with [1], [2], [3] matching the source numbers in context
3. If context does not contain enough information, say so explicitly
4. Use precise medical terminology appropriate for clinicians
5. If sources conflict with each other, point that out
6. Never fabricate drug names, dosages, or clinical recommendations
7. Keep the answer focused and clinically actionable"""


class Answer:
    """Holds a complete RAG answer with citations and confidence."""

    def __init__(self, question, text, citations,
                 conf_score, conf_label, sources_used):
        self.question     = question
        self.text         = text
        self.citations    = citations
        self.conf_score   = conf_score
        self.conf_label   = conf_label
        self.sources_used = sources_used
        self.disclaimer   = (
            "For educational purposes only. "
            "Always verify with current clinical guidelines."
        )

    def __repr__(self):
        lines = [
            f"\nQuestion: {self.question}",
            f"Confidence: {self.conf_label} ({int(self.conf_score*100)}%)",
            f"Sources: {', '.join(self.sources_used)}",
            f"\nAnswer:\n{self.text}",
            f"\nCitations:",
        ]
        for c in self.citations:
            lines.append(
                f"  [{c['num']}] {c['title']} | "
                f"{c['source'].upper()} | {c['year']} | "
                f"evidence={c['evidence_type']} | "
                f"conf={c['confidence']:.2f}"
            )
        lines.append(f"\n{self.disclaimer}")
        return "\n".join(lines)


class Retriever:
    """
    The full RAG pipeline in one class.

    Step 1: Embed the question
    Step 2: Search Pinecone for top-20 candidates
    Step 3: Score each chunk (similarity + evidence + recency)
    Step 4: Filter below MIN_SCORE, keep top 5
    Step 5: Build context string from top chunks
    Step 6: Send context + question to GPT-4o-mini
    Step 7: Return structured Answer with citations

    Why fetch 20 then keep 5?
    The most similar vector is not always the best evidence.
    A 2024 RCT at rank 8 should beat a 2001 case report at
    rank 1. We fetch a wide pool and rerank by confidence.
    """

    def __init__(self):
        self.embedder = Embedder()
        self.store    = PineconeStore()
        self.client   = OpenAI(api_key=settings.OPENAI_API_KEY)

    def query(self, question, source_filter=None, min_year=None):
        """
        Answer a clinical question using the RAG pipeline.

        Args:
            question:      clinical question from the user
            source_filter: limit to specific sources e.g. ["pubmed"]
            min_year:      only use evidence from this year onwards

        Returns:
            Answer object with text, citations, confidence
        """
        print(f"\n[Retriever] Question: {question}")

        # Step 1: Embed the question
        print(f"[Retriever] Embedding question...")
        query_vector = self.embedder.embed_one(question)

        # Step 2: Build optional Pinecone metadata filter
        filters = {}
        if source_filter:
            filters["source"] = {"$in": source_filter}
        if min_year:
            filters["year"]   = {"$gte": min_year}

        # Step 3: Search Pinecone for top 20 candidates
        print(f"[Retriever] Searching Pinecone...")
        matches = self.store.search(
            query_vector = query_vector,
            top_k        = 20,
            filters      = filters or None,
        )
        print(f"[Retriever] Got {len(matches)} candidates")

        if not matches:
            return self._no_data(question)

        # Step 4: Score and rerank by confidence
        # (similarity × 0.5) + (evidence weight × 0.3) + (recency × 0.2)
        for match in matches:
            match["confidence"] = score_chunk(
                match["score"],
                match["metadata"],
            )
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Filter below threshold, keep top 5
        top = [m for m in matches
               if m["confidence"] >= settings.MIN_SCORE][:5]

        # If nothing passes threshold, relax and take best available
        if not top:
            print(f"[Retriever] No chunks above MIN_SCORE={settings.MIN_SCORE}")
            print(f"[Retriever] Relaxing threshold, using top 3")
            top = matches[:3]

        print(f"[Retriever] Using top {len(top)} chunks after reranking")

        # Step 5: Build context string
        # Numbered [1], [2]... so GPT-4o-mini can cite them
        context_parts = []
        citations     = []

        for i, match in enumerate(top, 1):
            meta  = match["metadata"]
            text  = meta.get("text", "")
            title = meta.get("title", f"Source {i}")

            context_parts.append(
                f"[{i}] {title}\n"
                f"Source: {meta.get('source','').upper()} | "
                f"Type: {meta.get('evidence_type','')} | "
                f"Year: {meta.get('year','')} | "
                f"Confidence: {match['confidence']:.2f}\n"
                f"Content: {text}\n"
            )
            citations.append({
                "num":           i,
                "title":         title[:200],
                "source":        meta.get("source", ""),
                "evidence_type": meta.get("evidence_type", ""),
                "year":          meta.get("year", 0),
                "url":           meta.get("url", ""),
                "confidence":    match["confidence"],
            })

        context = "\n---\n".join(context_parts)

        # Step 6: Generate answer with GPT-4o-mini
        print(f"[Retriever] Generating answer with GPT-4o-mini...")
        response = self.client.chat.completions.create(
            model      = settings.CHAT_MODEL,
            max_tokens = 600,
            messages   = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": (
                    f"Question: {question}\n\n"
                    f"Evidence from medical knowledge base:\n\n"
                    f"{context}\n\n"
                    f"Answer using only the above evidence. "
                    f"Cite sources as [1], [2], etc."
                )},
            ],
        )
        answer_text = response.choices[0].message.content

        # Step 7: Compute overall confidence and return
        chunk_scores = [m["confidence"] for m in top]
        overall_conf = answer_confidence(chunk_scores)
        sources_used = list({m["metadata"].get("source", "") for m in top})

        return Answer(
            question     = question,
            text         = answer_text,
            citations    = citations,
            conf_score   = overall_conf,
            conf_label   = confidence_label(overall_conf),
            sources_used = sources_used,
        )

    def _no_data(self, question):
        """Safe fallback when nothing is found in the index."""
        return Answer(
            question     = question,
            text         = (
                "No relevant evidence found in the knowledge base. "
                "Try ingesting more data on this topic first:\n"
                "python3 scripts/ingest.py --source pubmed "
                f"--query \"{question}\" --max 50"
            ),
            citations    = [],
            conf_score   = 0.0,
            conf_label   = "No data",
            sources_used = [],
        )