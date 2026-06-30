# retrieval/confidence.py

from datetime import datetime
from config.settings import settings

CURRENT_YEAR = datetime.now().year


def score_chunk(similarity, metadata):
    """
    Computes a confidence score for one retrieved chunk.

    Why not just use the similarity score from Pinecone?
    Similarity alone tells you how close the chunk is to the
    query — but says nothing about how trustworthy the evidence
    is. A 2003 case report can score 0.82 similarity for a
    diabetes query, but a 2024 RCT on the same topic is far
    more clinically reliable.

    Formula:
      50% similarity   — how relevant is this chunk to the query?
      30% evidence     — how strong is the study design?
      20% recency      — how recent is the publication?

    Example:
      2024 RCT, similarity 0.80:
        0.80×0.5 + 0.85×0.3 + 1.00×0.2 = 0.855

      2003 case report, similarity 0.82:
        0.82×0.5 + 0.40×0.3 + 0.45×0.2 = 0.620

      The RCT ranks higher despite lower similarity — correct.
    """
    sim            = max(0.0, min(1.0, similarity))
    evidence_type  = metadata.get("evidence_type", "unknown")
    evidence_weight = settings.EVIDENCE_WEIGHTS.get(evidence_type, 0.50)
    year           = metadata.get("year", 0)
    recency_weight = _recency_weight(year)

    score = (sim * 0.50) + (evidence_weight * 0.30) + (recency_weight * 0.20)
    return round(min(score, 1.0), 4)


def answer_confidence(chunk_scores):
    """
    Combines individual chunk scores into one overall confidence.

    Why not just average?
    If chunk 1 scores 0.90 and chunks 2-5 score 0.50, the answer
    is mostly grounded in one strong source — it should score
    closer to 0.90 than the average of 0.60.

    We use decreasing weights: chunk 1 gets 1.0, chunk 2 gets
    0.5, chunk 3 gets 0.33. Strongest evidence has most influence.
    """
    if not chunk_scores:
        return 0.0

    top_scores   = sorted(chunk_scores, reverse=True)[:3]
    weights      = [1 / (i + 1) for i in range(len(top_scores))]
    weighted_sum = sum(s * w for s, w in zip(top_scores, weights))
    total_weight = sum(weights)

    return round(weighted_sum / total_weight, 4)


def confidence_label(score):
    """
    Converts a numeric score to a human-readable label.
    Shown in the UI so clinicians know how much to trust the answer.
    """
    if score >= 0.85:
        return "High"
    elif score >= 0.70:
        return "Moderate"
    elif score >= 0.55:
        return "Low"
    else:
        return "Very low — ingest more data on this topic"


def _recency_weight(year):
    """
    Returns a recency weight based on publication year.

    Why does recency matter in healthcare?
    Clinical guidelines change. A 2005 paper recommending a drug
    that was withdrawn in 2018 is dangerous to surface without
    context. Recent evidence reflects current best practice.
    """
    if not year or year < 1990:
        return 0.50

    age = CURRENT_YEAR - year

    if age <= 2:  return 1.00
    if age <= 5:  return 0.90
    if age <= 10: return 0.75
    if age <= 20: return 0.60
    return 0.45