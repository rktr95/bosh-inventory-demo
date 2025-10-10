from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.headers import RequestContext, require_headers
from app.db import compute_idempotency_key, get_database
from app.models import StockAdjustOut, StockAdjustRequest

router = APIRouter(prefix="/v1/stock", tags=["stock"])


@router.post("/adjust", response_model=StockAdjustOut)
async def adjust_stock(body: StockAdjustRequest, _ctx: RequestContext = Depends(require_headers)):
	db = get_database()
	key = compute_idempotency_key(body.sku, body.delta, body.transactionId)
	# Try to insert idempotency record. If duplicate, treat as already applied.
	try:
		await db.idempotency.insert_one({
			"_id": key,
			"sku": body.sku,
			"delta": body.delta,
			"transactionId": body.transactionId,
			"createdAt": datetime.now(timezone.utc),
		})
		should_apply = True
	except Exception:  # duplicate key -> do not apply again
		should_apply = False

	new_qty = None
	if should_apply:
		res = await db.stock.update_one(
			{"sku": body.sku},
			{"$inc": {"quantity": body.delta}, "$set": {"lastUpdated": datetime.now(timezone.utc)}},
			upsert=True,
		)
		# fetch the latest doc
		stock_doc = await db.stock.find_one({"sku": body.sku})
		new_qty = int(stock_doc.get("quantity", 0))
	else:
		stock_doc = await db.stock.find_one({"sku": body.sku})
		new_qty = int(stock_doc.get("quantity", 0)) if stock_doc else 0

	return StockAdjustOut(sku=body.sku, newQuantity=new_qty)

