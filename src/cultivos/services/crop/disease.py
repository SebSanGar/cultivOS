"""Pure disease/pest identification service — matches symptoms to known diseases."""


def identify_diseases(
    symptoms: list[str],
    diseases: list[dict],
    crop: str | None = None,
) -> list[dict]:
    """Match user-reported symptoms against known diseases.

    Args:
        symptoms: list of symptom strings (Spanish) reported by farmer
        diseases: list of disease dicts from DB (each has "symptoms", "affected_crops", etc.)
        crop: optional crop filter — only return diseases affecting this crop

    Returns:
        list of disease matches sorted by confidence (descending),
        each with added "confidence" and "symptoms_matched" fields
    """
    if not symptoms or not diseases:
        return []

    symptom_set = {s.lower().strip() for s in symptoms}
    matches = []

    for disease in diseases:
        # Filter by crop if specified
        if crop and crop.lower() not in [c.lower() for c in disease.get("affected_crops", [])]:
            continue

        disease_symptoms = {s.lower().strip() for s in disease.get("symptoms", [])}
        if not disease_symptoms:
            continue

        # Find overlapping symptoms
        matched = symptom_set & disease_symptoms
        if not matched:
            continue

        confidence = round(len(matched) / len(disease_symptoms), 2)

        matches.append({
            **disease,
            "confidence": confidence,
            "symptoms_matched": sorted(matched),
        })

    # Sort by confidence descending
    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches
