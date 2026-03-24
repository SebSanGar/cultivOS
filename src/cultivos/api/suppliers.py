"""Supplier and pricing API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.supplier import (
    IngredientPriceCreate,
    IngredientPriceRead,
    PriceComparison,
    SupplierCreate,
    SupplierRead,
)
from cultivos.services import supplier_service

router = APIRouter()


@router.post("/suppliers", response_model=SupplierRead, status_code=201)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    supplier = supplier_service.create_supplier(db, data)
    return _supplier_to_read(supplier)


@router.get("/suppliers", response_model=list[SupplierRead])
def list_suppliers(location_id: int = Query(...), db: Session = Depends(get_db)):
    suppliers = supplier_service.list_suppliers(db, location_id)
    return [_supplier_to_read(s) for s in suppliers]


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = supplier_service.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _supplier_to_read(supplier)


@router.post("/prices", response_model=IngredientPriceRead, status_code=201)
def log_price(data: IngredientPriceCreate, db: Session = Depends(get_db)):
    price = supplier_service.log_price(db, data)
    return IngredientPriceRead.model_validate(price)


@router.get("/ingredients/{ingredient_id}/prices", response_model=list[IngredientPriceRead])
def get_price_history(ingredient_id: int, db: Session = Depends(get_db)):
    prices = supplier_service.get_price_history(db, ingredient_id)
    return [IngredientPriceRead.model_validate(p) for p in prices]


@router.get("/ingredients/{ingredient_id}/compare", response_model=PriceComparison)
def compare_prices(ingredient_id: int, db: Session = Depends(get_db)):
    return supplier_service.compare_prices(db, ingredient_id)


def _supplier_to_read(supplier) -> SupplierRead:
    return SupplierRead(
        id=supplier.id,
        name=supplier.name,
        contact_name=supplier.contact_name,
        contact_email=supplier.contact_email,
        contact_phone=supplier.contact_phone,
        address=supplier.address,
        categories=json.loads(supplier.categories_json or "[]"),
        reliability_score=supplier.reliability_score,
        quality_rating=supplier.quality_rating,
        price_competitiveness=supplier.price_competitiveness,
        payment_terms=supplier.payment_terms,
        minimum_order=supplier.minimum_order,
        relationship_status=supplier.relationship_status,
        location_id=supplier.location_id,
        created_at=supplier.created_at,
    )
