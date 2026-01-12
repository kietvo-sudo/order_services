from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.models import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=schemas.ProductOut,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: schemas.ProductCreate, db: Session = Depends(get_db)
):
    """
    Create product. Product ID will be auto-generated.
    """
    product = crud.create_product(db, payload)
    return product


@router.get("", response_model=List[schemas.ProductOut])
def list_products(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.patch("/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: str, payload: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    updated = crud.update_product(db, product, payload)
    return updated


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    crud.delete_product(db, product)

