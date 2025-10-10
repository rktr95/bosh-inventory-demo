from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.headers import RequestContext, require_headers
from app.db import get_database
from app.models import ProductCreate, ProductOut

router = APIRouter(prefix="/v1/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductCreate, _ctx: RequestContext = Depends(require_headers)):
	db = get_database()
	doc = {
		"sku": body.sku,
		"name": body.name,
		"price": body.price,
		"currency": body.currency.value,
		"createdAt": datetime.now(timezone.utc),
	}
	try:
		await db.products.insert_one(doc)
	except DuplicateKeyError:
		raise HTTPException(status_code=409, detail="SKU already exists")
	return ProductOut(**doc)


@router.get("/{sku}", response_model=ProductOut)
async def get_product(sku: str, _ctx: RequestContext = Depends(require_headers)):
	db = get_database()
	doc = await db.products.find_one({"sku": sku}, {"_id": 0})
	if not doc:
		raise HTTPException(status_code=404, detail="Product not found")
	return ProductOut(**doc)

