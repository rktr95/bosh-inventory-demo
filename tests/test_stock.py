import os
import pytest
from httpx import AsyncClient

from app.main import app
from app.db import connect_to_mongo, close_mongo_connection, get_database


@pytest.fixture(autouse=True, scope="module")
async def setup_mongo():
	os.environ["MONGODB_URL"] = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
	os.environ["MONGODB_DB"] = "inventory_test"
	await connect_to_mongo()
	yield
	db = get_database()
	await db.products.delete_many({})
	await db.stock.delete_many({})
	await db.idempotency.delete_many({})
	await close_mongo_connection()


def auth_headers():
	return {"X-Client-Source": "tests"}


@pytest.mark.asyncio
async def test_stock_adjust_idempotent():
	async with AsyncClient(app=app, base_url="http://test") as client:
		# Ensure product exists (not strictly required for stock collection)
		await client.post("/v1/products", json={"sku": "S-1", "name": "P", "price": 1.0, "currency": "USD"}, headers=auth_headers())

		payload = {"sku": "S-1", "delta": 5, "transactionId": "tid-1"}
		r1 = await client.post("/v1/stock/adjust", json=payload, headers=auth_headers())
		assert r1.status_code == 200
		first_qty = r1.json()["newQuantity"]

		# repeat same idempotency key
		r2 = await client.post("/v1/stock/adjust", json=payload, headers=auth_headers())
		assert r2.status_code == 200
		second_qty = r2.json()["newQuantity"]

		assert second_qty == first_qty

		# apply different tx id -> should increase again
		r3 = await client.post("/v1/stock/adjust", json={"sku": "S-1", "delta": 5, "transactionId": "tid-2"}, headers=auth_headers())
		assert r3.status_code == 200
		third_qty = r3.json()["newQuantity"]
		assert third_qty == first_qty + 5

