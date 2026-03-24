"""
Culinary intelligence — pure functions for DishDNA, technique audit, DNA comparison.

No DB, no HTTP. Data in, results out.
"""

import math


def compute_complexity_score(num_techniques: int, num_ingredients: int, num_steps: int) -> int:
    """Complexity score 1-10 based on technique count, ingredient count, and step count."""
    raw = (num_techniques * 2) + (num_ingredients * 0.5) + (num_steps * 0.3)
    return min(10, max(1, round(raw)))


def generate_dish_dna(
    technique_ids: list[int],
    technique_data: list[dict],
    num_ingredients: int,
    num_steps: int,
    cuisine_influences: list[str] | None = None,
    seasonal_peak: str | None = None,
) -> dict:
    """Generate a DishDNA fingerprint from recipe data.

    Args:
        technique_ids: ordered list of technique IDs used in recipe
        technique_data: list of dicts with keys: id, flavor_impact, texture_impact
        num_ingredients: count of ingredients
        num_steps: count of recipe steps
        cuisine_influences: optional list of cuisine tags
        seasonal_peak: optional season string

    Returns:
        dict with keys: technique_fingerprint, flavor_profile, texture_profile,
        cuisine_influences, seasonal_peak, complexity_score
    """
    complexity = compute_complexity_score(len(technique_ids), num_ingredients, num_steps)

    # Aggregate flavor/texture profiles from techniques
    flavor_profile = _aggregate_flavor_profile(technique_data)
    texture_profile = _aggregate_texture_profile(technique_data)

    return {
        "technique_fingerprint": technique_ids,
        "flavor_profile": flavor_profile,
        "texture_profile": texture_profile,
        "cuisine_influences": cuisine_influences or [],
        "seasonal_peak": seasonal_peak,
        "complexity_score": complexity,
    }


def compare_dna(dna_a: dict, dna_b: dict) -> float:
    """Compare two DishDNA fingerprints. Returns 0-1 similarity score.

    Weighted: 40% technique Jaccard + 30% flavor cosine + 30% texture cosine.
    """
    # Technique fingerprint: Jaccard similarity
    set_a = set(dna_a.get("technique_fingerprint", []))
    set_b = set(dna_b.get("technique_fingerprint", []))
    jaccard = _jaccard_similarity(set_a, set_b)

    # Flavor profile: cosine similarity
    flavor_sim = _cosine_similarity(
        dna_a.get("flavor_profile", {}),
        dna_b.get("flavor_profile", {}),
    )

    # Texture profile: cosine similarity
    texture_sim = _cosine_similarity(
        dna_a.get("texture_profile", {}),
        dna_b.get("texture_profile", {}),
    )

    return round(0.4 * jaccard + 0.3 * flavor_sim + 0.3 * texture_sim, 4)


def technique_audit(
    all_techniques: list[dict],
    in_use_ids: set[int],
) -> dict:
    """Audit technique diversity across the menu.

    Args:
        all_techniques: list of dicts with keys: id, name, category
        in_use_ids: set of technique IDs currently linked to recipes

    Returns:
        dict with: overall_score, by_category, total_techniques, in_use_count,
        underused (list), suggestions (list)
    """
    by_category: dict[str, list[dict]] = {}
    for t in all_techniques:
        cat = t["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(t)

    category_scores = {}
    underused = []
    suggestions = []

    for cat, techs in by_category.items():
        used = [t for t in techs if t["id"] in in_use_ids]
        score = (len(used) / len(techs)) * 10 if techs else 0
        category_scores[cat] = round(score, 1)

        unused = [t for t in techs if t["id"] not in in_use_ids]
        underused.extend(unused)

        if score < 5 and unused:
            suggestions.append(
                f"Add a {cat} technique like {unused[0]['name']}"
            )

    overall = round(sum(category_scores.values()) / len(category_scores), 1) if category_scores else 0

    return {
        "overall_score": overall,
        "by_category": category_scores,
        "total_techniques": len(all_techniques),
        "in_use_count": len(in_use_ids & {t["id"] for t in all_techniques}),
        "underused": underused,
        "suggestions": suggestions,
    }


def dna_comparison_matrix(dna_list: list[dict]) -> list[dict]:
    """Generate pairwise similarity for all DNA in a list.

    Each dict in dna_list should have: recipe_id, recipe_name, and DNA fields.
    Returns list of {recipe_a_id, recipe_a_name, recipe_b_id, recipe_b_name, similarity}.
    """
    pairs = []
    for i in range(len(dna_list)):
        for j in range(i + 1, len(dna_list)):
            sim = compare_dna(dna_list[i], dna_list[j])
            pairs.append({
                "recipe_a_id": dna_list[i]["recipe_id"],
                "recipe_a_name": dna_list[i].get("recipe_name"),
                "recipe_b_id": dna_list[j]["recipe_id"],
                "recipe_b_name": dna_list[j].get("recipe_name"),
                "similarity": sim,
            })
    return pairs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _cosine_similarity(profile_a: dict, profile_b: dict) -> float:
    """Cosine similarity between two dicts of numeric values."""
    all_keys = set(list(profile_a.keys()) + list(profile_b.keys()))
    if not all_keys:
        return 0.0

    dot = sum(profile_a.get(k, 0) * profile_b.get(k, 0) for k in all_keys)
    mag_a = math.sqrt(sum(profile_a.get(k, 0) ** 2 for k in all_keys))
    mag_b = math.sqrt(sum(profile_b.get(k, 0) ** 2 for k in all_keys))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# Flavor impact keywords -> profile dimension mapping
_FLAVOR_KEYWORDS = {
    "savory": ["sear", "roast", "braise", "saute", "deglaze", "caramelize", "grill", "smoke"],
    "sweet": ["caramelize", "glaze", "reduce"],
    "acid": ["pickle", "cure", "ceviche", "deglaze"],
    "bitter": ["char", "grill", "smoke"],
    "umami": ["braise", "sear", "roast", "confit", "smoke"],
}

_TEXTURE_KEYWORDS = {
    "crispy": ["sear", "crisp", "grill", "roast", "fry"],
    "creamy": ["emulsify", "puree", "confit"],
    "chewy": ["braise", "sous vide"],
    "tender": ["braise", "sous vide", "confit", "poach"],
}


def _aggregate_flavor_profile(technique_data: list[dict]) -> dict[str, float]:
    """Build flavor profile from technique names/impacts."""
    profile = {"savory": 0, "sweet": 0, "acid": 0, "bitter": 0, "umami": 0}
    for t in technique_data:
        name_lower = (t.get("name") or "").lower()
        impact_lower = (t.get("flavor_impact") or "").lower()
        combined = f"{name_lower} {impact_lower}"
        for dimension, keywords in _FLAVOR_KEYWORDS.items():
            for kw in keywords:
                if kw in combined:
                    profile[dimension] = min(10, profile[dimension] + 3)
    return profile


def _aggregate_texture_profile(technique_data: list[dict]) -> dict[str, float]:
    """Build texture profile from technique names/impacts."""
    profile = {"crispy": 0, "creamy": 0, "chewy": 0, "tender": 0}
    for t in technique_data:
        name_lower = (t.get("name") or "").lower()
        impact_lower = (t.get("texture_impact") or "").lower()
        combined = f"{name_lower} {impact_lower}"
        for dimension, keywords in _TEXTURE_KEYWORDS.items():
            for kw in keywords:
                if kw in combined:
                    profile[dimension] = min(10, profile[dimension] + 3)
    return profile
