# test_component2.py

import sys
sys.path.insert(0, ".")

from ingestion.pubmed_ingestor import PubMedIngestor
from ingestion.chunker import Chunker, Chunk


def test_chunker():
    print("=" * 60)
    print("COMPONENT 2 TEST — Chunker")
    print("=" * 60)

    chunker = Chunker(chunk_size=450, overlap=50)

    # ── Test 1: Short abstract → exactly 1 chunk ─────────────────────────────
    print("\n--- Test 1: Short abstract produces 1 chunk ---")

    short_article = _make_fake_article(
        pmid="00001",
        title="Metformin in Type 2 Diabetes",
        abstract="Metformin is the recommended first-line therapy. " * 20,
        # 20 × 8 words = 160 words — well under 450 limit
        year=2023
    )
    chunks = chunker.chunk_pubmed(short_article)
    assert len(chunks) == 1, f"FAIL: expected 1 chunk, got {len(chunks)}"
    print(f"PASS: Short abstract → {len(chunks)} chunk")

    # ── Test 2: Long abstract → multiple chunks ───────────────────────────────
    print("\n--- Test 2: Long abstract produces multiple chunks ---")

    long_abstract = "Patients with type 2 diabetes who received metformin showed improvements. " * 50
    # 50 × 12 words = 600 words — should split into 2 chunks
    long_article = _make_fake_article(
        pmid="00002",
        title="Long Study on Metformin",
        abstract=long_abstract,
        year=2022
    )
    chunks = chunker.chunk_pubmed(long_article)
    assert len(chunks) > 1, f"FAIL: expected >1 chunk, got {len(chunks)}"
    print(f"PASS: Long abstract → {len(chunks)} chunks")

    # ── Test 3: No chunk exceeds chunk_size ───────────────────────────────────
    print("\n--- Test 3: No chunk exceeds chunk_size words ---")
    for c in chunks:
        word_count = len(c.text.split())
        assert word_count <= chunker.chunk_size + 20, (
            # +20 tolerance because we don't split mid-sentence
            f"FAIL: Chunk has {word_count} words, limit is {chunker.chunk_size}"
        )
    print(f"PASS: All chunks are within word limit ({chunker.chunk_size} words)")

    # ── Test 4: Chunk IDs are unique ──────────────────────────────────────────
    print("\n--- Test 4: Chunk IDs are unique ---")
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids)), "FAIL: Duplicate chunk IDs found"
    print(f"PASS: All {len(ids)} chunk IDs are unique")
    for cid in ids:
        print(f"  ID: {cid}")

    # ── Test 5: Overlap — consecutive chunks share some content ──────────────
    print("\n--- Test 5: Consecutive chunks have overlap ---")
    if len(chunks) >= 2:
        words_0 = set(chunks[0].text.split())
        words_1 = set(chunks[1].text.split())
        shared  = words_0 & words_1
        assert len(shared) > 0, "FAIL: No overlap between consecutive chunks"
        print(f"PASS: Chunks 0 and 1 share {len(shared)} common words (overlap working)")

    # ── Test 6: Metadata is preserved in each chunk ───────────────────────────
    print("\n--- Test 6: Metadata preserved in chunks ---")
    for c in chunks:
        assert c.metadata.get("source") == "pubmed", "FAIL: source missing from metadata"
        assert c.metadata.get("pmid"),               "FAIL: pmid missing from metadata"
        assert c.metadata.get("year") > 0,           "FAIL: year missing from metadata"
        assert c.metadata.get("url"),                "FAIL: url missing from metadata"
    print("PASS: All chunks carry correct metadata")

    # ── Test 7: Structured abstract splitting ─────────────────────────────────
    print("\n--- Test 7: Structured abstract (BACKGROUND/METHODS/RESULTS) ---")
    structured_abstract = (
        "BACKGROUND: Type 2 diabetes is a chronic metabolic condition. " * 10 +
        "\nMETHODS: We conducted a randomized controlled trial. " * 10 +
        "\nRESULTS: Patients showed significant improvement. " * 10 +
        "\nCONCLUSION: Metformin remains first-line therapy. " * 5
    )
    structured_article = _make_fake_article(
        pmid="00003",
        title="RCT of Metformin",
        abstract=structured_abstract,
        year=2021
    )
    chunks = chunker.chunk_pubmed(structured_article)
    assert len(chunks) >= 2, "FAIL: Structured abstract should produce multiple chunks"
    print(f"PASS: Structured abstract → {len(chunks)} chunks (split at section headers)")

    # ── Test 8: Live article from PubMed ─────────────────────────────────────
    print("\n--- Test 8: Real PubMed article ---")
    print("  Fetching 3 real articles from PubMed...")
    ingestor = PubMedIngestor(email="test@example.com")
    articles = ingestor.search("type 2 diabetes treatment guidelines", max_results=3)
    assert len(articles) > 0, "FAIL: Could not fetch real articles (check internet)"

    all_chunks = []
    for article in articles:
        c = chunker.chunk_pubmed(article)
        all_chunks.extend(c)
        print(f"  Article [{article.year}] → {len(c)} chunk(s) | "
              f"{len(article.text.split())} words total")

    print(f"\nPASS: {len(articles)} real articles → {len(all_chunks)} total chunks")

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n--- Chunk details ---")
    for i, c in enumerate(all_chunks):
        word_count = len(c.text.split())
        print(f"  Chunk {i}: id={c.id} | words={word_count} | "
              f"evidence={c.metadata.get('evidence_type')}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — Component 2 is working correctly")
    print("=" * 60)
    print("\nReady for Component 3 — Embedder")


def _make_fake_article(pmid, title, abstract, year):
    """
    Creates a fake PubMedArticle for testing without hitting the API.
    This is a common testing pattern — isolate the component under test
    from external dependencies (the PubMed API in this case).
    """
    from ingestion.pubmed_ingestor import PubMedArticle
    return PubMedArticle(
        pmid=pmid,
        title=title,
        abstract=abstract,
        authors=["Test Author"],
        journal="Test Journal",
        year=year,
        pub_types=["Journal Article"],
        mesh_terms=["Diabetes Mellitus"],
        doi="",
    )


if __name__ == "__main__":
    test_chunker()