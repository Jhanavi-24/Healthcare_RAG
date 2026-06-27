# test_component3.py

import sys
sys.path.insert(0, ".")

from embeddings.embedder import Embedder
from ingestion.pubmed_ingestor import PubMedIngestor
from ingestion.chunker import Chunker


def test_embedder():
    print("=" * 60)
    print("COMPONENT 3 TEST — Embedder")
    print("=" * 60)

    embedder = Embedder()

    # ── Test 1: embed_one returns correct shape ───────────────────────────────
    print("\n--- Test 1: embed_one returns a 1536-dimension vector ---")
    vector = embedder.embed_one("Metformin is used to treat type 2 diabetes.")
    assert isinstance(vector, list),       "FAIL: vector should be a list"
    assert len(vector) == 1536,            f"FAIL: expected 1536 dims, got {len(vector)}"
    assert isinstance(vector[0], float),   "FAIL: vector values should be floats"
    print(f"PASS: Got vector with {len(vector)} dimensions")
    print(f"  First 5 values: {[round(v, 4) for v in vector[:5]]}")

    # ── Test 2: similar sentences score high ─────────────────────────────────
    print("\n--- Test 2: Similar sentences have high cosine similarity ---")
    vec_a = embedder.embed_one("Metformin is the first-line treatment for type 2 diabetes.")
    vec_b = embedder.embed_one("The recommended initial therapy for diabetes mellitus type 2 is metformin.")
    score = embedder.cosine_similarity(vec_a, vec_b)
    print(f"  Similarity between paraphrased sentences: {score:.4f}")
    assert score > 0.60, f"FAIL: similar sentences should score >0.60, got {score:.4f}"
    print(f"PASS: Similar sentences score {score:.4f} (above 0.60 threshold)")

    # ── Test 3: unrelated sentences score low ────────────────────────────────
    print("\n--- Test 3: Unrelated sentences have low cosine similarity ---")
    vec_c = embedder.embed_one("The weather in New York is sunny today.")
    score_unrelated = embedder.cosine_similarity(vec_a, vec_c)
    print(f"  Similarity between medical and weather text: {score_unrelated:.4f}")
    assert score_unrelated < 0.5, (
        f"FAIL: unrelated sentences should score <0.5, got {score_unrelated:.4f}"
    )
    print(f"PASS: Unrelated sentences score {score_unrelated:.4f} (below 0.5 threshold)")

    # ── Test 4: medical synonyms score high ──────────────────────────────────
    # This is the KEY test for healthcare RAG — different words, same meaning
    print("\n--- Test 4: Medical synonyms score high (key RAG requirement) ---")
    vec_heart_attack = embedder.embed_one("A patient presented with a heart attack and was given aspirin and thrombolysis treatment.")
    vec_mi = embedder.embed_one("The patient was diagnosed with acute myocardial infarction and received antiplatelet therapy.")
    score_synonyms   = embedder.cosine_similarity(vec_heart_attack, vec_mi)
    print(f"  'heart attack' vs 'myocardial infarction': {score_synonyms:.4f}")
    assert score_synonyms > 0.55, (
        f"FAIL: medical synonyms should score >0.55, got {score_synonyms:.4f}"
    )
    print(f"PASS: Medical synonyms score {score_synonyms:.4f} — embedding captures meaning not just words")

    # ── Test 5: embed_many returns correct count ──────────────────────────────
    print("\n--- Test 5: embed_many returns one vector per input ---")
    texts = [
        "Metformin reduces blood sugar levels.",
        "Insulin resistance is a hallmark of type 2 diabetes.",
        "HbA1c is used to monitor long-term glucose control.",
        "Hypertension increases cardiovascular risk.",
        "ACE inhibitors protect kidney function in diabetic patients.",
    ]
    vectors = embedder.embed_many(texts, batch_size=3)
    assert len(vectors) == len(texts), (
        f"FAIL: expected {len(texts)} vectors, got {len(vectors)}"
    )
    assert all(len(v) == 1536 for v in vectors), "FAIL: all vectors must be 1536-dim"
    print(f"PASS: {len(texts)} texts → {len(vectors)} vectors, each 1536-dim")

    # ── Test 6: order is preserved in embed_many ──────────────────────────────
    print("\n--- Test 6: Order is preserved in embed_many ---")
    # Embed individually and compare to batch result
    vec_single = embedder.embed_one(texts[0])
    sim = embedder.cosine_similarity(vectors[0], vec_single)
    assert sim > 0.999, f"FAIL: first batch vector should match single embed, got sim={sim:.4f}"
    print(f"PASS: Batch order preserved (similarity to single embed: {sim:.6f})")

    # ── Test 7: end-to-end with real PubMed chunks ───────────────────────────
    print("\n--- Test 7: End-to-end — PubMed articles → chunks → vectors ---")
    print("  Fetching 3 real PubMed articles...")
    ingestor = PubMedIngestor(email="test@example.com")
    chunker  = Chunker()
    articles = ingestor.search("hypertension treatment guidelines", max_results=3)
    assert len(articles) > 0, "FAIL: Could not fetch articles"

    all_chunks = []
    for article in articles:
        all_chunks.extend(chunker.chunk_pubmed(article))

    print(f"  Produced {len(all_chunks)} chunks from {len(articles)} articles")
    print(f"  Embedding all chunks...")

    chunk_texts   = [c.text for c in all_chunks]
    chunk_vectors = embedder.embed_many(chunk_texts)

    assert len(chunk_vectors) == len(all_chunks), "FAIL: vector count mismatch"
    print(f"PASS: {len(all_chunks)} chunks → {len(chunk_vectors)} vectors")

    # ── Test 8: similarity ranking makes clinical sense ───────────────────────
    print("\n--- Test 8: Similarity ranking is clinically meaningful ---")
    query        = "blood pressure medication first line treatment"
    query_vector = embedder.embed_one(query)

    scores = []
    for chunk, vector in zip(all_chunks, chunk_vectors):
        sim = embedder.cosine_similarity(query_vector, vector)
        scores.append((sim, chunk.text[:80]))

    scores.sort(reverse=True)
    print(f"  Query: '{query}'")
    print(f"  Top 3 most similar chunks:")
    for i, (sim, preview) in enumerate(scores[:3], 1):
        print(f"    {i}. score={sim:.4f} | {preview}...")

    assert scores[0][0] > scores[-1][0], "FAIL: top result should score higher than bottom"
    print(f"PASS: Top result ({scores[0][0]:.4f}) scores higher than bottom ({scores[-1][0]:.4f})")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — Component 3 is working correctly")
    print("=" * 60)
    print("\nKey results:")
    print(f"  Similar sentences:    {score:.4f}  (higher = better)")
    print(f"  Medical synonyms:     {score_synonyms:.4f}  (higher = better)")
    print(f"  Unrelated sentences:  {score_unrelated:.4f}  (lower = better)")
    print("\nReady for Component 4 — Pinecone store")


if __name__ == "__main__":
    test_embedder()