from __future__ import annotations

import hashlib
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_MONGO_URL_ENV = "MONGODB_URL"
_DEFAULT_URL = "mongodb://localhost:27017"
_DB_NAME = os.getenv("MONGODB_DB", "inventory_db")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_database() -> AsyncIOMotorDatabase:
	assert _db is not None, "Database not initialized"
	return _db


async def connect_to_mongo() -> None:
	global _client, _db
	print("Env passed mongo url is ......... ", _MONGO_URL_ENV)
	mongo_url = os.getenv(_MONGO_URL_ENV, _DEFAULT_URL)
	print("Connecting to MongoDB... and inv is ......... ", mongo_url)
 
	_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=3000)
	_db = _client[_DB_NAME]

	# Indexes
	await _db.products.create_index("sku", unique=True)
	# TTL on idempotency createdAt 60s
	await _db.idempotency.create_index("createdAt", expireAfterSeconds=60)
	# _id is unique by default; we'll store hash as _id


async def close_mongo_connection() -> None:
	global _client, _db
	if _client is not None:
		_client.close()
	_client = None
	_db = None


def compute_idempotency_key(sku: str, delta: int, transaction_id: str) -> str:
	payload = f"{sku}|{delta}|{transaction_id}".encode()
	return hashlib.sha256(payload).hexdigest()

