"""Crop problem diagnosis service — phrase-to-treatment pipeline.

Pure function: no HTTP, no DB access. DB queries happen in the route handler.
"""

from cultivos.services.intelligence.recommendations import recommend_treatment, Treatment


# Keyword → approximate health score for treatment generation when no DB context
_KEYWORD_HEALTH_MAP: dict[str, float] = {
    "plaga": 40.0,       # pest
    "amarillo": 50.0,    # yellowing
    "amarillando": 50.0,
    "seco": 45.0,        # drying
    "secando": 45.0,
    "marchito": 40.0,    # wilting
    "moho": 35.0,        # mold
    "hongo": 35.0,       # fungus
    "enfermedad": 40.0,  # disease
    "raiz": 45.0,        # root issue
    "muerto": 30.0,      # dying
    "petateó": 30.0,     # colloquial for died/wilting
    "petateando": 30.0,
}

_DEFAULT_HEALTH_SCORE = 55.0  # triggers some recommendations
_HEALTHY_THRESHOLD = 80.0


def _word_overlap_score(phrase: str, candidate: str) -> int:
    """Count shared words between phrase and candidate (case-insensitive)."""
    phrase_words = set(phrase.lower().split())
    candidate_words = set(candidate.lower().split())
    return len(phrase_words & candidate_words)


def _infer_health_from_phrase(phrase: str) -> float:
    """Estimate health score from phrase keywords for treatment generation."""
    phrase_lower = phrase.lower()
    for keyword, score in _KEYWORD_HEALTH_MAP.items():
        if keyword in phrase_lower:
            return score
    return _DEFAULT_HEALTH_SCORE


def diagnose(
    phrase: str,
    crop: str | None,
    vocab_entries: list,  # list of FarmerVocabulary ORM objects
    health_score: float | None,
) -> dict:
    """Match farmer phrase to vocabulary, then generate treatment recommendations.

    Args:
        phrase: Colloquial phrase from farmer (e.g. "se está amarillando el maíz")
        crop: Optional crop type to scope matching (e.g. "maiz")
        vocab_entries: All FarmerVocabulary records (pre-fetched by route)
        health_score: Latest field health score (None if field_id not provided or not found)

    Returns:
        dict with: matched_phrase, formal_term_es, likely_cause, recommended_action, treatments
    """
    phrase_lower = phrase.lower().strip()
    best_match = None
    best_score = 0

    for entry in vocab_entries:
        # Exact phrase match gets top priority base score
        if entry.phrase.lower() == phrase_lower:
            overlap = 1000
        else:
            overlap = _word_overlap_score(phrase_lower, entry.phrase.lower())

        # Crop scoping: prefer crop-matching entries
        if crop and entry.crop and entry.crop.lower() != crop.lower():
            overlap -= 1

        if overlap > best_score:
            best_score = overlap
            best_match = entry

    # Build response fields from matched entry
    matched_phrase = None
    formal_term_es = None
    likely_cause = None
    recommended_action = None

    if best_match and best_score > 0:
        matched_phrase = best_match.phrase
        formal_term_es = best_match.formal_term_es
        likely_cause = best_match.likely_cause
        recommended_action = best_match.recommended_action

    # Determine health score for treatment generation
    if health_score is not None:
        effective_score = health_score
    else:
        effective_score = _infer_health_from_phrase(phrase)

    # Generate treatments using existing recommendation engine
    treatments: list[Treatment] = recommend_treatment(
        health_score=effective_score,
        crop_type=crop,
    )

    return {
        "matched_phrase": matched_phrase,
        "formal_term_es": formal_term_es,
        "likely_cause": likely_cause,
        "recommended_action": recommended_action,
        "treatments": [dict(t) for t in treatments],
    }
