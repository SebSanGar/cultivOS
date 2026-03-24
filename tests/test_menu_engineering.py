"""Tests for menu engineering classification."""

from decimal import Decimal

from cultivos.services.menu_engineering_service import (
    classify_menu_item,
    build_menu_matrix,
    food_cost_percentage,
)


def test_classify_star():
    result = classify_menu_item(
        margin=Decimal("15"), popularity=100,
        avg_margin=Decimal("10"), avg_popularity=Decimal("50"),
    )
    assert result == "star"


def test_classify_puzzle():
    result = classify_menu_item(
        margin=Decimal("15"), popularity=10,
        avg_margin=Decimal("10"), avg_popularity=Decimal("50"),
    )
    assert result == "puzzle"


def test_classify_plowhorse():
    result = classify_menu_item(
        margin=Decimal("5"), popularity=100,
        avg_margin=Decimal("10"), avg_popularity=Decimal("50"),
    )
    assert result == "plowhorse"


def test_classify_dog():
    result = classify_menu_item(
        margin=Decimal("5"), popularity=10,
        avg_margin=Decimal("10"), avg_popularity=Decimal("50"),
    )
    assert result == "dog"


def test_build_matrix():
    items = [
        {"recipe_id": 1, "recipe_name": "Star Dish", "food_cost": "5", "menu_price": "25", "popularity": 100},
        {"recipe_id": 2, "recipe_name": "Dog Dish", "food_cost": "10", "menu_price": "12", "popularity": 5},
        {"recipe_id": 3, "recipe_name": "Plowhorse", "food_cost": "10", "menu_price": "12", "popularity": 100},
        {"recipe_id": 4, "recipe_name": "Puzzle", "food_cost": "3", "menu_price": "25", "popularity": 5},
    ]
    matrix = build_menu_matrix(items)
    assert matrix.stars == 1
    assert matrix.dogs == 1
    assert matrix.plowhorses == 1
    assert matrix.puzzles == 1
    assert len(matrix.items) == 4


def test_food_cost_percentage():
    result = food_cost_percentage(Decimal("30"), Decimal("100"))
    assert result == Decimal("30.00")


def test_food_cost_zero_revenue():
    result = food_cost_percentage(Decimal("30"), Decimal("0"))
    assert result == Decimal("0")
