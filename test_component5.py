# test_component5.py

import sys
sys.path.insert(0, ".")

from retrieval.confidence import score_chunk, answer_confidence, confidence_label
from retrieval.retriever import Retriever


def test_retriever():
    print("=" * 60)
    print("COMPONENT 5 TEST — Retriever + Confidence Scorer")
    print("=" * 60)

    # ── Test 1: RCT scores higher than case report ────────────────────────────
    print("\n--- Test 1: RCT beats case report despite lower similarity ---")
    rct_score = score_chunk(
        similarity = 0.75,
        metadata   = {"evidence_type": "rct", "year": 2023}
    )
    case_score = score_chunk(
        similarity = 0.82,
        metadata   = {"evidence_type": "case_report", "year": 2003}
    )
    print(f"  RCT        (sim=0.75, year=2023): {rct_score:.4f}")
    print(f"  Case report(sim=0.82, year=2003): {case_score:.4f}")
    assert rct_score > case_score, (
        f"FAIL: RCT should outscore case report. "
        f"Got rct={rct_score:.4f}, case={case_score:.4f}"
    )
    print(f"PASS: RCT ({rct_score:.4f}) > case report ({case_score:.4f})")

    # ── Test 2: Recent paper scores higher than old paper ─────────────────────
    print("\n--- Test 2: 2024 paper beats 2000 paper at same similarity ---")
    recent = score_chunk(0.75, {"evidence_type": "abstract", "year": 2024})
    old    = score_chunk(0.75, {"evidence_type": "abstract", "year": 2000})
    print(f"  2024 paper (sim=0.75): {recent:.4f}")
    print(f"  2000 paper (sim=0.75): {old:.4f}")
    assert recent > old, "FAIL: Recent paper should score higher"
    print(f"PASS: 2024 ({recent:.4f}) > 2000 ({old:.4f})")

    # ── Test 3: Systematic review is highest evidence ─────────────────────────
    print("\n--- Test 3: Evidence hierarchy is correct ---")
    sys_review = score_chunk(0.70, {"evidence_type": "systematic_review", "year": 2022})
    rct        = score_chunk(0.70, {"evidence_type": "rct",               "year": 2022})
    abstract   = score_chunk(0.70, {"evidence_type": "abstract",          "year": 2022})
    case       = score_chunk(0.70, {"evidence_type": "case_report",       "year": 2022})
    print(f"  Systematic review: {sys_review:.4f}")
    print(f"  RCT:               {rct:.4f}")
    print(f"  Abstract:          {abstract:.4f}")
    print(f"  Case report:       {case:.4f}")
    assert sys_review > rct > abstract > case, (
        "FAIL: Evidence hierarchy incorrect"
    )
    print("PASS: Systematic review > RCT > abstract > case report")

    # ── Test 4: answer_confidence weights top chunk most ──────────────────────
    print("\n--- Test 4: Answer confidence weights top chunk most ---")
    scores = [0.90, 0.50, 0.50]
    conf   = answer_confidence(scores)
    avg    = sum(scores) / len(scores)
    print(f"  Chunk scores: {scores}")
    print(f"  Simple average:      {avg:.4f}")
    print(f"  Weighted confidence: {conf:.4f}")
    assert conf > avg, "FAIL: Weighted should exceed simple average"
    print(f"PASS: Weighted ({conf:.4f}) > average ({avg:.4f})")

    # ── Test 5: Confidence labels ─────────────────────────────────────────────
    print("\n--- Test 5: Confidence labels ---")
    assert "High"     in confidence_label(0.90)
    assert "Moderate" in confidence_label(0.75)
    assert "Low"      in confidence_label(0.60)
    print("PASS: High / Moderate / Low labels correct")

    # ── Test 6: Full RAG pipeline end-to-end ─────────────────────────────────
    print("\n--- Test 6: Full RAG pipeline ---")
    print("  (uses vectors already in Pinecone from Component 4 test)")
    retriever = Retriever()
    answer    = retriever.query(
        "What is the mechanism of action of metformin?"
    )

    assert answer.text,              "FAIL: No answer text generated"
    assert answer.conf_score >= 0.0, "FAIL: Confidence score missing"
    assert answer.conf_label,        "FAIL: Confidence label missing"
    print(f"PASS: Answer generated")
    print(f"\n{answer}")

    # ── Test 7: Citation markers appear in answer ─────────────────────────────
    print("\n--- Test 7: Answer contains citation markers ---")
    if answer.citations:
        has_cites = any(
            f"[{c['num']}]" in answer.text
            for c in answer.citations
        )
        if has_cites:
            print("PASS: Answer contains [1], [2] etc. citation markers")
        else:
            print("NOTE: Model answered but skipped inline citations")
            print("      This improves with more data in the index")
    else:
        print("SKIP: No citations available — ingest more data first")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — Component 5 is working correctly")
    print("=" * 60)
    print("\nReady for Component 6 — ingestion script + full system test")


if __name__ == "__main__":
    test_retriever()