"""Supplier and pricing service — CRUD and price intelligence."""

import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from cultivos.db.models import Ingredient, IngredientPrice, Supplier
from cultivos.models.supplier import (
    IngredientPriceCreate,
    PriceComparison,
    SupplierCreate,
    SupplierPrice,
)


def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    supplier = Supplier(
        name=data.name,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        address=data.address,
        categories_json=json.dumps(data.categories),
        payment_terms=data.payment_terms,
        minimum_order=data.minimum_order,
        location_id=data.location_id,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def list_suppliers(db: Session, location_id: int) -> list[Supplier]:
    return (
        db.query(Supplier)
        .filter(Supplier.location_id == location_id, Supplier.deleted_at.is_(None))
        .order_by(Supplier.name)
        .all()
    )


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    return db.query(Supplier).filter(
        Supplier.id == supplier_id, Supplier.deleted_at.is_(None)
    ).first()


def log_price(db: Session, data: IngredientPriceCreate) -> IngredientPrice:
    price = IngredientPrice(
        ingredient_id=data.ingredient_id,
        supplier_id=data.supplier_id,
        price_per_unit=data.price_per_unit,
        unit=data.unit,
        quoted_price=data.quoted_price,
        invoice_price=data.invoice_price,
        volume_tier=data.volume_tier,
        delivery_terms=data.delivery_terms,
        notes=data.notes,
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


def get_price_history(db: Session, ingredient_id: int, limit: int = 20) -> list[IngredientPrice]:
    return (
        db.query(IngredientPrice)
        .filter(IngredientPrice.ingredient_id == ingredient_id)
        .order_by(IngredientPrice.effective_date.desc())
        .limit(limit)
        .all()
    )


def compare_prices(db: Session, ingredient_id: int) -> PriceComparison:
    """Get latest price from each supplier for an ingredient."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()

    # Get all prices, group by supplier, take latest
    all_prices = (
        db.query(IngredientPrice)
        .filter(IngredientPrice.ingredient_id == ingredient_id)
        .order_by(IngredientPrice.effective_date.desc())
        .all()
    )

    seen_suppliers: set[int] = set()
    supplier_prices: list[SupplierPrice] = []
    for p in all_prices:
        if p.supplier_id not in seen_suppliers:
            seen_suppliers.add(p.supplier_id)
            supplier = db.query(Supplier).filter(Supplier.id == p.supplier_id).first()
            supplier_prices.append(SupplierPrice(
                supplier_id=p.supplier_id,
                supplier_name=supplier.name if supplier else "Unknown",
                price_per_unit=Decimal(str(p.price_per_unit)),
                unit=p.unit,
                effective_date=p.effective_date,
            ))

    # Sort by price ascending (cheapest first)
    supplier_prices.sort(key=lambda sp: sp.price_per_unit)

    return PriceComparison(
        ingredient_id=ingredient_id,
        ingredient_name=ingredient.name if ingredient else None,
        prices=supplier_prices,
    )
