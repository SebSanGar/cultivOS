"""Unit tests for culinary intelligence pure functions."""

from cultivos.services.intelligence_service import (
    compare_dna,
    compute_complexity_score,
    dna_comparison_matrix,
    generate_dish_dna,
    technique_audit,
)


class TestComplexityScore:
    def test_simple_dish(self):
        # 2 techniques, 4 ingredients, 3 steps = 2*2 + 4*0.5 + 3*0.3 = 6.9 -> 7
        score = compute_complexity_score(2, 4, 3)
        assert score == 7

    def test_complex_dish(self):
        # 6 techniques, 12 ingredients, 10 steps = 12 + 6 + 3 = 21 -> capped at 10
        score = compute_complexity_score(6, 12, 10)
        assert score == 10

    def test_minimal_dish(self):
        # 1 technique, 2 ingredients, 1 step = 2 + 1 + 0.3 = 3.3 -> 3
        score = compute_complexity_score(1, 2, 1)
        assert score == 3

    def test_floor_at_1(self):
        score = compute_complexity_score(0, 0, 0)
        assert score == 1


class TestGenerateDNA:
    def test_generates_fingerprint(self):
        techniques = [
            {"id": 1, "name": "Grill", "flavor_impact": "Smoky char", "texture_impact": "Crispy exterior"},
            {"id": 2, "name": "Compose", "flavor_impact": None, "texture_impact": None},
        ]
        dna = generate_dish_dna(
            technique_ids=[1, 2],
            technique_data=techniques,
            num_ingredients=5,
            num_steps=4,
        )
        assert dna["technique_fingerprint"] == [1, 2]
        assert dna["complexity_score"] == 8  # 2*2 + 5*0.5 + 4*0.3 = 7.7 -> 8
        assert "savory" in dna["flavor_profile"]
        assert "crispy" in dna["texture_profile"]


class TestCompareDNA:
    def test_identical_dna(self):
        dna = {
            "technique_fingerprint": [1, 2, 3],
            "flavor_profile": {"savory": 6, "sweet": 0, "acid": 3, "bitter": 3, "umami": 6},
            "texture_profile": {"crispy": 6, "creamy": 0, "chewy": 0, "tender": 0},
        }
        assert compare_dna(dna, dna) == 1.0

    def test_completely_different(self):
        dna_a = {
            "technique_fingerprint": [1, 2],
            "flavor_profile": {"savory": 10, "sweet": 0},
            "texture_profile": {"crispy": 10, "creamy": 0},
        }
        dna_b = {
            "technique_fingerprint": [3, 4],
            "flavor_profile": {"savory": 0, "sweet": 10},
            "texture_profile": {"crispy": 0, "creamy": 10},
        }
        sim = compare_dna(dna_a, dna_b)
        assert sim < 0.1  # very different

    def test_partial_overlap(self):
        dna_a = {
            "technique_fingerprint": [1, 2, 3],
            "flavor_profile": {"savory": 6, "sweet": 2},
            "texture_profile": {"crispy": 6, "tender": 2},
        }
        dna_b = {
            "technique_fingerprint": [2, 3, 4],
            "flavor_profile": {"savory": 4, "sweet": 4},
            "texture_profile": {"crispy": 4, "tender": 4},
        }
        sim = compare_dna(dna_a, dna_b)
        assert 0.3 < sim < 0.9

    def test_empty_dna(self):
        dna_a = {"technique_fingerprint": [], "flavor_profile": {}, "texture_profile": {}}
        dna_b = {"technique_fingerprint": [], "flavor_profile": {}, "texture_profile": {}}
        sim = compare_dna(dna_a, dna_b)
        # Jaccard(empty, empty) = 1.0, cosine(empty, empty) = 0.0
        # Weighted: 0.4*1 + 0.3*0 + 0.3*0 = 0.4
        assert sim == 0.4


class TestTechniqueAudit:
    def test_full_coverage(self):
        techs = [
            {"id": 1, "name": "Grill", "category": "Heat"},
            {"id": 2, "name": "Sear", "category": "Heat"},
        ]
        result = technique_audit(techs, {1, 2})
        assert result["overall_score"] == 10.0
        assert result["in_use_count"] == 2
        assert len(result["underused"]) == 0

    def test_low_coverage(self):
        techs = [
            {"id": 1, "name": "Grill", "category": "Heat"},
            {"id": 2, "name": "Sear", "category": "Heat"},
            {"id": 3, "name": "Roast", "category": "Heat"},
            {"id": 4, "name": "Braise", "category": "Heat"},
            {"id": 5, "name": "Emulsify", "category": "Texture"},
        ]
        result = technique_audit(techs, {1})
        assert result["overall_score"] < 5.0
        assert result["in_use_count"] == 1
        assert len(result["underused"]) == 4

    def test_identifies_underused(self):
        techs = [
            {"id": 1, "name": "Grill", "category": "Heat"},
            {"id": 2, "name": "Sear", "category": "Heat"},
            {"id": 3, "name": "Pickle", "category": "Preservation"},
        ]
        result = technique_audit(techs, {1})
        underused_ids = {t["id"] for t in result["underused"]}
        assert 2 in underused_ids
        assert 3 in underused_ids

    def test_generates_suggestions(self):
        techs = [
            {"id": 1, "name": "Grill", "category": "Heat"},
            {"id": 2, "name": "Pickle", "category": "Preservation"},
        ]
        result = technique_audit(techs, set())
        assert len(result["suggestions"]) >= 1
        assert "Preservation" in result["suggestions"][0] or "Heat" in result["suggestions"][0]


class TestDNAMatrix:
    def test_generates_all_pairs(self):
        dnas = [
            {"recipe_id": 1, "recipe_name": "A", "technique_fingerprint": [1], "flavor_profile": {"savory": 5}, "texture_profile": {"crispy": 5}},
            {"recipe_id": 2, "recipe_name": "B", "technique_fingerprint": [2], "flavor_profile": {"sweet": 5}, "texture_profile": {"creamy": 5}},
            {"recipe_id": 3, "recipe_name": "C", "technique_fingerprint": [1, 2], "flavor_profile": {"savory": 3, "sweet": 3}, "texture_profile": {"crispy": 3, "creamy": 3}},
        ]
        pairs = dna_comparison_matrix(dnas)
        assert len(pairs) == 3  # C(3,2) = 3 pairs

    def test_empty_list(self):
        assert dna_comparison_matrix([]) == []
