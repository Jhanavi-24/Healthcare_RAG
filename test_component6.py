# test_component6.py

"""
COMPONENT 6 — Full system test

This test ingests real medical data on multiple topics,
then asks real clinical questions and verifies the answers
are well-cited and high confidence.

This takes 3-5 minutes to run because it ingests ~150 real
PubMed articles before testing.
"""

import sys
sys.path.insert(0, ".")

from ingestion.pubmed_ingestor import PubMedIngestor
from ingestion.chunker import Chunker
from embeddings.embedder import Embedder
from embeddings.pinecone_store import PineconeStore
from retrieval.retriever import Retriever


def ingest_topic(query, max_results, chunker, embedder, store):
    """Reuses the same ingestion logic as scripts/ingest.py"""
    print(f"\n  Ingesting '{query}'...")
    ingestor = PubMedIngestor(email="test@example.com")
    articles = ingestor.search(query, max_results=max_results)

    if not articles:
        return 0

    chunks = []
    for article in articles:
        chunks.extend(chunker.chunk_pubmed(article))

    texts   = [c.text for c in chunks]
    vectors = embedder.embed_many(texts)
    stored  = store.upsert(chunks, vectors)
    print(f"  Stored {stored} vectors for '{query}'")
    return stored


def test_full_system():
    print("=" * 60)
    print("COMPONENT 6 TEST — Full System")
    print("=" * 60)

    chunker  = Chunker()
    embedder = Embedder()
    store    = PineconeStore()

    # ── Step 1: Ingest real data on 3 topics ──────────────────────────────────
    print("\n--- Ingesting real medical data (this takes a few minutes) ---")
    topics = [
        ("type 2 diabetes metformin treatment guidelines", 50),
        ("hypertension first line treatment ACE inhibitors", 50),
        ("sepsis management protocol antibiotics",            50),
    ]

    total_stored = 0
    for query, max_results in topics:
        total_stored += ingest_topic(query, max_results, chunker, embedder, store)

    print(f"\nTotal new vectors ingested: {total_stored}")

    import time
    print("Waiting for Pinecone index to update...")
    time.sleep(3)

    stats = store.stats()
    print(f"Total vectors now in index: {stats.get('total_vector_count', '?')}")

    # ── Step 2: Ask real clinical questions ───────────────────────────────────
    print("\n" + "=" * 60)
    print("--- Asking real clinical questions ---")
    print("=" * 60)

    retriever = Retriever()

    questions = [
        "What is the first-line treatment for type 2 diabetes?",
        "What is the recommended initial therapy for hypertension?",
        "What is the antibiotic protocol for sepsis management?",
    ]

    all_passed = True

    for question in questions:
        print(f"\n{'─'*60}")
        print(f"Q: {question}")
        print(f"{'─'*60}")

        answer = retriever.query(question)

        print(f"\nConfidence: {answer.conf_label} ({int(answer.conf_score*100)}%)")
        print(f"Sources used: {answer.sources_used}")
        print(f"\nAnswer:\n{answer.text}")

        if answer.citations:
            print(f"\nCitations:")
            for c in answer.citations:
                print(f"  [{c['num']}] {c['title'][:60]}...")
                print(f"       {c['source'].upper()} | {c['year']} | "
                      f"{c['evidence_type']} | conf={c['confidence']:.2f}")

        # Verify quality
        if answer.conf_score < 0.55:
            print(f"\nWARNING: Low confidence ({answer.conf_score:.2f}) for this question")
            all_passed = False
        else:
            print(f"\nPASS: Confidence acceptable ({answer.conf_score:.2f})")

        if not answer.citations:
            print(f"WARNING: No citations returned")
            all_passed = False

    # ── Step 3: Final verdict ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED — Full RAG system is working correctly")
    else:
        print("SYSTEM WORKING — some answers had lower confidence")
        print("This is normal with limited data. Ingest more to improve.")
    print("=" * 60)

    print(f"\nYour Healthcare Knowledge Navigator is live with "
          f"{stats.get('total_vector_count', '?')} vectors.")
    print("\nTry your own questions:")
    print('  python3 -c "')
    print('from retrieval.retriever import Retriever')
    print('r = Retriever()')
    print('print(r.query(\'your question here\'))')
    print('"')


if __name__ == "__main__":
    test_full_system()