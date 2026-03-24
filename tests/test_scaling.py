"""Tests for non-linear recipe scaling — the intelligence layer."""

from decimal import Decimal

from cultivos.services.scaling_service import scale_ingredient, scale_recipe, scale_cooking_time


class TestScaleIngredient:
    def test_linear_scaling(self):
        result = scale_ingredient(Decimal("100"), Decimal("20"), "linear", Decimal("1.0"))
        assert result == Decimal("2000.0000")

    def test_linear_scale_factor_1(self):
        result = scale_ingredient(Decimal("100"), Decimal("1"), "linear", Decimal("1.0"))
        assert result == Decimal("100")

    def test_sublinear_scaling_salt(self):
        """Salt at exponent 0.8 should scale LESS than linear."""
        linear = scale_ingredient(Decimal("10"), Decimal("20"), "linear", Decimal("1.0"))
        sublinear = scale_ingredient(Decimal("10"), Decimal("20"), "sublinear", Decimal("0.8"))
        assert sublinear < linear
        assert sublinear > Decimal("10")  # still more than base

    def test_fixed_scaling(self):
        """Fixed ingredients (vanilla, bay leaf) stay the same at any scale."""
        result = scale_ingredient(Decimal("5"), Decimal("100"), "fixed")
        assert result == Decimal("5")

    def test_stepped_scaling_eggs(self):
        """Eggs: 3 base, scale 2.3x -> linear=6.9, step_size=1 -> ceil to 7."""
        result = scale_ingredient(
            Decimal("3"), Decimal("2.3"), "stepped",
            step_size=Decimal("1"),
        )
        assert result == Decimal("7.0000")

    def test_stepped_scaling_sheets(self):
        """Phyllo sheets: 5 base, scale 3x -> 15, step_size=5 -> 15."""
        result = scale_ingredient(
            Decimal("5"), Decimal("3"), "stepped",
            step_size=Decimal("5"),
        )
        assert result == Decimal("15.0000")

    def test_stepped_rounds_up(self):
        """5 sheets * 2.1 = 10.5 -> ceil(10.5/5)*5 = 15."""
        result = scale_ingredient(
            Decimal("5"), Decimal("2.1"), "stepped",
            step_size=Decimal("5"),
        )
        assert result == Decimal("15.0000")

    def test_logarithmic_scaling_chili(self):
        """Chili at exponent 0.5 should scale much less than linear."""
        linear = scale_ingredient(Decimal("10"), Decimal("10"), "linear", Decimal("1.0"))
        log = scale_ingredient(Decimal("10"), Decimal("10"), "logarithmic", Decimal("0.5"))
        assert log < linear
        # At exponent 0.5: 10 * 10^0.5 = 10 * 3.162 = 31.62
        assert Decimal("31") < log < Decimal("32")


class TestScaleRecipe:
    def test_scales_multiple_ingredients(self):
        ingredients = [
            {"ingredient_id": 1, "ingredient_name": "Flour", "amount": Decimal("500"), "unit": "g", "scaling_type": "linear"},
            {"ingredient_id": 2, "ingredient_name": "Salt", "amount": Decimal("10"), "unit": "g", "scaling_type": "sublinear"},
            {"ingredient_id": 3, "ingredient_name": "Vanilla", "amount": Decimal("5"), "unit": "mL", "scaling_type": "fixed"},
        ]
        rules = {
            2: {"rule_type": "sublinear", "exponent": Decimal("0.8"), "step_size": None},
        }

        result = scale_recipe(ingredients, base_yield=10, target_yield=100, scaling_rules=rules)

        assert len(result) == 3
        flour = next(r for r in result if r.ingredient_id == 1)
        salt = next(r for r in result if r.ingredient_id == 2)
        vanilla = next(r for r in result if r.ingredient_id == 3)

        assert flour.scaled_amount == Decimal("5000.0000")  # linear 10x
        assert salt.scaled_amount < Decimal("100.0000")  # less than linear
        assert vanilla.scaled_amount == Decimal("5")  # fixed

    def test_identity_scaling(self):
        ingredients = [
            {"ingredient_id": 1, "ingredient_name": "Flour", "amount": Decimal("500"), "unit": "g", "scaling_type": "linear"},
        ]
        result = scale_recipe(ingredients, base_yield=10, target_yield=10)
        assert result[0].scaled_amount == Decimal("500")


class TestScaleCookingTime:
    def test_larger_batch_takes_longer(self):
        result = scale_cooking_time(30, Decimal("10"))
        assert result > 30

    def test_same_batch_same_time(self):
        result = scale_cooking_time(30, Decimal("1"))
        assert result == 30

    def test_none_time(self):
        result = scale_cooking_time(None, Decimal("10"))
        assert result == 0
