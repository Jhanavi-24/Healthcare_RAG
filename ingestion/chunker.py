# ingestion/chunker.py

import re


class Chunk:
    """
    Represents one piece of text that will become one vector in Pinecone.

    Why a class and not just a string?
    Each chunk needs to carry two things:
    1. text      — what gets embedded (sent to OpenAI)
    2. metadata  — what gets stored alongside the vector in Pinecone
                   (title, year, URL, evidence type, etc.)
    3. id        — a unique string Pinecone uses to identify this vector

    If we just stored the text, we'd lose all context about where it came
    from. When we retrieve it later, we'd have no way to show the user
    which article it came from or link them to the source.
    """

    def __init__(self, text, metadata, chunk_index=0):
        self.text        = text
        self.metadata    = metadata
        self.chunk_index = chunk_index   # 0 for first chunk, 1 for second, etc.

    @property
    def id(self):
        """
        Unique ID for this vector in Pinecone.

        Format: {source}_{document_id}_c{chunk_index}
        Example: pubmed_38291453_c0
                 pubmed_38291453_c1  (second chunk of same article)

        Why does uniqueness matter?
        Pinecone uses upsert — if you run ingestion twice, it overwrites
        vectors with the same ID instead of creating duplicates. So consistent
        IDs mean re-running is always safe.

        We sanitize the doc_id because Pinecone IDs cannot contain
        spaces, slashes, or special characters.
        """
        source = self.metadata.get("source", "doc")
        doc_id = (
            self.metadata.get("pmid")
            or self.metadata.get("nct_id")
            or self.metadata.get("brand_name", "unknown")
        )
        # Replace anything that isn't a letter, digit, or underscore
        safe_id = re.sub(r"[^\w]", "_", str(doc_id))[:40]
        return f"{source}_{safe_id}_c{self.chunk_index}"

    def __repr__(self):
        word_count = len(self.text.split())
        return (
            f"Chunk(id={self.id}, words={word_count}, "
            f"evidence={self.metadata.get('evidence_type', '?')})"
        )


class Chunker:
    """
    Splits medical documents into embedding-sized pieces.

    The core tension in chunking:
    - Too large  → imprecise retrieval, may hit token limits
    - Too small  → loses context, fragments sentences mid-thought

    Sweet spot for medical abstracts: 400–500 words per chunk.
    That is roughly 500–650 tokens — well within the 8192-token
    limit of text-embedding-3-small, and specific enough for
    targeted retrieval.

    Overlap explained:
    Imagine a 900-word abstract split at word 500 with no overlap.
    If a key sentence spans words 490–510, it gets split in half —
    the first chunk ends mid-thought, the second starts mid-thought.
    A 50-word overlap means words 450–500 appear in BOTH chunks,
    so neither chunk loses that sentence's context.
    """

    def __init__(self, chunk_size=450, overlap=50):
        """
        chunk_size: target word count per chunk
        overlap:    how many words to repeat between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.overlap    = overlap

    # ── Public methods — one per document type ────────────────────────────────

    def chunk_pubmed(self, article):
        text     = article.text
        metadata = article.metadata()

        # Always try header-based splitting FIRST for structured abstracts
        # We do this before the length check because a structured abstract
        # should be split by section even if it's short — each section
        # answers a different clinical question and should be independently
        # retrievable
        sections = self._split_on_headers(text)
        if len(sections) > 1:
            chunks = []
            for i, section in enumerate(sections):
                if section.strip():
                    chunks.append(Chunk(
                        text=section.strip(),
                        metadata={**metadata, "section": f"part_{i}"},
                        chunk_index=i,
                    ))
            return chunks

        # No headers found — check if short enough for a single chunk
        word_count = len(text.split())
        if word_count <= self.chunk_size:
            return [Chunk(text=text, metadata=metadata, chunk_index=0)]

        # Long and no headers — use sliding window
        return self._sliding_window(text, metadata)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _split_on_headers(self, text):
        """
        Splits text at structured abstract section headers.

        Matches patterns like:
          BACKGROUND:   Background:   OBJECTIVE:   Methods:
          RESULTS:      Conclusion:   CONCLUSIONS:

        The (?=...) is a lookahead — it splits BEFORE the header word
        so the header stays attached to its section instead of being
        orphaned at the end of the previous section.
        """
        header_pattern = re.compile(
            r'\n(?='
            r'(?:BACKGROUND|OBJECTIVE|METHODS?|RESULTS?|CONCLUSION|CONCLUSIONS?|'
            r'DISCUSSION|INTRODUCTION|PURPOSE|SETTING|PARTICIPANTS?|'
            r'INTERVENTIONS?|FINDINGS?|SIGNIFICANCE|LIMITATIONS?)'
            r'[\s:])',
            re.IGNORECASE
        )
        return header_pattern.split(text)

    def _split_sentences(self, text):
        """
        Splits text into individual sentences.

        The challenge: abbreviations contain dots too.
        "Dr. Smith found that vs. placebo the result was significant."
        A naive split on "." would break after "Dr" and "vs".

        We protect common medical abbreviations by temporarily replacing
        their dots, then split, then restore them.
        """
        # Protect abbreviations — replace their dots temporarily
        abbreviations = [
            "Dr", "Mr", "Mrs", "Ms", "Prof", "vs", "et al",
            "Fig", "No", "Vol", "approx", "dept", "esp",
            "Jan", "Feb", "Mar", "Apr", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            "mg", "kg", "mL", "IV", "p.o", "b.i.d", "t.i.d",
        ]
        protected = text
        for abbr in abbreviations:
            protected = protected.replace(f"{abbr}.", f"{abbr}DOTPROTECTED")

        # Split on sentence-ending punctuation followed by a capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)

        # Restore the dots we protected
        sentences = [s.replace("DOTPROTECTED", ".") for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    def _sliding_window(self, text, metadata):
        """
        Splits long text into overlapping chunks using a sliding window.

        Algorithm:
        1. Split text into sentences
        2. Accumulate sentences until we hit chunk_size words
        3. Save that group as a chunk
        4. Back up by `overlap` words (keep the last few sentences)
        5. Continue accumulating from there

        This guarantees:
        - Every chunk is <= chunk_size words
        - Consecutive chunks share ~overlap words of context
        - No sentence is split in the middle
        """
        sentences  = self._split_sentences(text)
        chunks     = []
        current    = []       # sentences in the current chunk
        word_count = 0
        chunk_idx  = 0

        for sentence in sentences:
            words = sentence.split()

            # If adding this sentence exceeds chunk_size AND we have content,
            # save what we have and start a new chunk with overlap
            if word_count + len(words) > self.chunk_size and current:

                # Save current chunk
                chunk_text = " ".join(current)
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata=metadata,
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1

                # Build overlap: walk backwards through current sentences
                # until we've collected ~self.overlap words
                overlap_sentences = []
                overlap_words     = 0
                for sent in reversed(current):
                    overlap_words += len(sent.split())
                    if overlap_words >= self.overlap:
                        break
                    overlap_sentences.insert(0, sent)

                # Start the new chunk from the overlap sentences
                current    = overlap_sentences
                word_count = sum(len(s.split()) for s in current)

            current.append(sentence)
            word_count += len(words)

        # Don't forget the last chunk (the loop ends before saving it)
        if current:
            chunks.append(Chunk(
                text=" ".join(current),
                metadata=metadata,
                chunk_index=chunk_idx,
            ))

        return chunks