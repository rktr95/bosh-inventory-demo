import asyncio
import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.db import connect_to_mongo, close_mongo_connection, get_database


@pytest.fixture(autouse=True, scope="module")
async def setup_mongo():
	os.environ["MONGODB_URL"] = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
	os.environ["MONGODB_DB"] = "inventory_test"
	await connect_to_mongo()
	yield
	# cleanup
	db = get_database()
	await db.products.delete_many({})
	await db.stock.delete_many({})
	await db.idempotency.delete_many({})
	await close_mongo_connection()


def auth_headers():
	return {"X-Client-Source": "tests"}


@pytest.mark.asyncio
async def test_create_product_and_get():
	async with AsyncClient(app=app, base_url="http://test") as client:
		payload = {"sku": "T-1", "name": "Test", "price": 1.0, "currency": "USD"}
		res = await client.post("/v1/products", json=payload, headers=auth_headers())
		assert res.status_code == status.HTTP_201_CREATED, res.text
		data = res.json()
		assert data["sku"] == "T-1"

		res2 = await client.get("/v1/products/T-1", headers=auth_headers())
		assert res2.status_code == 200
		assert res2.json()["sku"] == "T-1"


@pytest.mark.asyncio
async def test_validation_negative_price():
	async with AsyncClient(app=app, base_url="http://test") as client:
		payload = {"sku": "T-2", "name": "Test", "price": -1.0, "currency": "USD"}
		res = await client.post("/v1/products", json=payload, headers=auth_headers())
		assert res.status_code in (400, 422)
		body = res.json()
		assert "StatusCode" in body and "Message" in body


@pytest.mark.asyncio
async def test_duplicate_sku_conflict():
	async with AsyncClient(app=app, base_url="http://test") as client:
		payload = {"sku": "T-dup", "name": "Test", "price": 1.0, "currency": "USD"}
		res1 = await client.post("/v1/products", json=payload, headers=auth_headers())
		assert res1.status_code == 201
		res2 = await client.post("/v1/products", json=payload, headers=auth_headers())
		assert res2.status_code == 409
		body = res2.json()
		assert body["StatusCode"] == 409


@pytest.mark.asyncio
async def test_get_missing_product_404():
	async with AsyncClient(app=app, base_url="http://test") as client:
		res = await client.get("/v1/products/does-not-exist", headers=auth_headers())
		assert res.status_code == 404
		body = res.json()
		assert body["StatusMessage"] == "Not Found"

