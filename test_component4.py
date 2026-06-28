# test_component4.py

import sys
sys.path.insert(0, ".")

from ingestion.pubmed_ingestor import PubMedIngestor
from ingestion.chunker import Chunker
from embeddings.embedder import Embedder
from embeddings.pinecone_store import PineconeStore


def test_pinecone():
    print("=" * 60)
    print("COMPONENT 4 TEST — Pinecone Store")
    print("=" * 60)

    store    = PineconeStore()
    embedder = Embedder()
    chunker  = Chunker()

    # ── Test 1: Index exists and is reachable ─────────────────────────────────
    print("\n--- Test 1: Index is reachable ---")
    try:
        st = store.stats()
        print(f"PASS: Connected to index '{store.index_name}'")
        print(f"  Vectors before test: {st.get('total_vector_count', 0)}")
    except Exception as e:
        print(f"FAIL: Cannot reach Pinecone index: {e}")
        print("Run: python3 scripts/setup.py first")
        sys.exit(1)

    # ── Test 2: Fetch real articles and store them ────────────────────────────
    print("\n--- Test 2: Ingest 5 real PubMed articles into Pinecone ---")
    ingestor = PubMedIngestor(email="test@example.com")
    articles = ingestor.search("type 2 diabetes metformin", max_results=5)
    assert len(articles) > 0, "FAIL: No articles fetched"

    # Chunk them
    all_chunks = []
    for article in articles:
        all_chunks.extend(chunker.chunk_pubmed(article))
    print(f"  {len(articles)} articles → {len(all_chunks)} chunks")

    # Embed them
    print(f"  Embedding {len(all_chunks)} chunks...")
    texts   = [c.text for c in all_chunks]
    vectors = embedder.embed_many(texts)

    # Store in Pinecone
    stored = store.upsert(all_chunks, vectors)
    assert stored > 0, "FAIL: No vectors stored"
    print(f"PASS: Stored {stored} vectors in Pinecone")

    # ── Test 3: Vector count increased ───────────────────────────────────────
    print("\n--- Test 3: Vector count increased after upsert ---")
    import time
    time.sleep(2)   # Pinecone index updates are not instant — wait 2 seconds
    st_after = store.stats()
    count    = st_after.get("total_vector_count", 0)
    assert count > 0, "FAIL: Index still shows 0 vectors"
    print(f"PASS: Index now contains {count} vectors")

    # ── Test 4: Search returns relevant results ───────────────────────────────
    print("\n--- Test 4: Search returns relevant results ---")
    query        = "metformin first line treatment type 2 diabetes"
    query_vector = embedder.embed_one(query)
    results      = store.search(query_vector, top_k=3)

    assert len(results) > 0,   "FAIL: Search returned no results"
    assert results[0]["score"] > 0.5, (
        f"FAIL: Top result score too low: {results[0]['score']:.4f}"
    )
    print(f"PASS: Search returned {len(results)} results")
    print(f"\n  Query: '{query}'")
    print(f"\n  Top results:")
    for i, r in enumerate(results, 1):
        title = r["metadata"].get("title", "no title")[:60]
        score = r["score"]
        year  = r["metadata"].get("year", "?")
        src   = r["metadata"].get("source", "?")
        print(f"    {i}. score={score:.4f} | [{year}] {title}...")
        print(f"       source={src} | id={r['id']}")

    # ── Test 5: Results are sorted by score (best first) ─────────────────────
    print("\n--- Test 5: Results are sorted best-first ---")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), (
        "FAIL: Results not sorted by score descending"
    )
    print(f"PASS: Scores in order: {[round(s, 4) for s in scores]}")

    # ── Test 6: Metadata is returned correctly ────────────────────────────────
    print("\n--- Test 6: Metadata present in results ---")
    top = results[0]["metadata"]
    required_keys = ["source", "title", "year", "evidence_type", "url", "text"]
    for key in required_keys:
        assert key in top, f"FAIL: metadata missing key '{key}'"
    print(f"PASS: All metadata keys present")
    print(f"  Source:        {top.get('source')}")
    print(f"  Year:          {top.get('year')}")
    print(f"  Evidence type: {top.get('evidence_type')}")
    print(f"  URL:           {top.get('url')}")
    print(f"  Text preview:  {top.get('text', '')[:100]}...")

    # ── Test 7: Metadata filter works ────────────────────────────────────────
    print("\n--- Test 7: Metadata filter works ---")
    results_filtered = store.search(
        query_vector,
        top_k=5,
        filters={"source": {"$in": ["pubmed"]}},
    )
    for r in results_filtered:
        assert r["metadata"].get("source") == "pubmed", (
            f"FAIL: Filter returned non-pubmed result: {r['metadata'].get('source')}"
        )
    print(f"PASS: Filter returned only pubmed results ({len(results_filtered)} total)")

    # ── Test 8: Upsert is idempotent (safe to run twice) ─────────────────────
    print("\n--- Test 8: Re-ingesting same articles doesn't create duplicates ---")
    count_before = store.stats().get("total_vector_count", 0)
    store.upsert(all_chunks, vectors)   # ingest the same chunks again
    time.sleep(2)
    count_after = store.stats().get("total_vector_count", 0)
    assert count_after == count_before, (
        f"FAIL: Count changed from {count_before} to {count_after} — duplicates created"
    )
    print(f"PASS: Count stayed at {count_after} — upsert is idempotent")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — Component 4 is working correctly")
    print("=" * 60)
    print(f"\nPinecone index '{store.index_name}' has {count_after} vectors")
    print("Ready for Component 5 — Retriever")


if __name__ == "__main__":
    test_pinecone()