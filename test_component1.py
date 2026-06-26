# test_component1.py

import sys
sys.path.insert(0, ".")   # lets Python find the ingestion/ folder

from ingestion.pubmed_ingestor import PubMedIngestor

def test_pubmed():
    print("=" * 60)
    print("COMPONENT 1 TEST — PubMed Ingestor")
    print("=" * 60)

    ingestor = PubMedIngestor(email="jhanaviputcha957@gmail.com")  # put your real email here

    # Fetch just 5 articles to keep the test fast
    articles = ingestor.search("type 2 diabetes metformin treatment", max_results=5)

    # ── Test 1: Did we get any articles? ─────────────────────────────────────
    print("\n--- Test 1: Got articles? ---")
    assert len(articles) > 0, "FAIL: No articles returned"
    print(f"PASS: Got {len(articles)} articles")

    # ── Test 2: Check each article has the fields we need ────────────────────
    print("\n--- Test 2: Fields present? ---")
    for i, article in enumerate(articles):
        assert article.pmid,     f"FAIL: Article {i} has no PMID"
        assert article.title,    f"FAIL: Article {i} has no title"
        assert article.abstract, f"FAIL: Article {i} has no abstract"
        assert article.year > 0, f"FAIL: Article {i} has no year"
    print("PASS: All articles have pmid, title, abstract, year")

    # ── Test 3: Print first article so you can visually verify ───────────────
    print("\n--- Test 3: Visual check — first article ---")
    a = articles[0]
    print(f"  PMID:     {a.pmid}")
    print(f"  Title:    {a.title}")
    print(f"  Year:     {a.year}")
    print(f"  Journal:  {a.journal}")
    print(f"  Authors:  {', '.join(a.authors[:3])}")
    print(f"  Type:     {a.evidence_type}")
    print(f"  Abstract: {a.abstract[:300]}...")

    # ── Test 4: Check the .text property (used by embedder later) ────────────
    print("\n--- Test 4: .text property ---")
    assert a.text.startswith("Title:"),    "FAIL: .text should start with 'Title:'"
    assert "Abstract:" in a.text,         "FAIL: .text should contain 'Abstract:'"
    print("PASS: .text property is correctly formatted")
    print(f"  Preview: {a.text[:200]}...")

    # ── Test 5: Check metadata dict (used by Pinecone later) ─────────────────
    print("\n--- Test 5: .metadata() dict ---")
    meta = a.metadata()
    required_keys = ["source", "pmid", "title", "year", "evidence_type", "url"]
    for key in required_keys:
        assert key in meta, f"FAIL: metadata missing key '{key}'"
    assert meta["source"] == "pubmed",         "FAIL: source should be 'pubmed'"
    assert meta["url"].startswith("https://"), "FAIL: url should start with https://"
    print("PASS: metadata() has all required keys")
    print(f"  URL: {meta['url']}")
    print(f"  Evidence type: {meta['evidence_type']}")

    # ── Test 6: Print all articles in summary ────────────────────────────────
    print("\n--- Test 6: All articles summary ---")
    for i, art in enumerate(articles, 1):
        print(f"  {i}. [{art.year}] {art.evidence_type:20s} | {art.title[:60]}...")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — Component 1 is working correctly")
    print("=" * 60)

if __name__ == "__main__":
    test_pubmed()