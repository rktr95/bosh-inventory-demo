# Inventory Service

FastAPI + Motor (MongoDB) Inventory API with consistent error envelopes, generalized headers, idempotent stock adjustments, Docker Compose, and tests.

## Requirements
- Python 3.10+
- Poetry
- Docker + docker-compose

## Setup (Poetry)
```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Environment variables:
- `MONGODB_URL` (default `mongodb://localhost:27017`)
- `MONGODB_DB` (default `inventory_db`)

## Docker Compose
```bash
cd deploy
docker-compose up -d
# App: http://localhost:8000/docs
```

## Headers
- Required: `X-Client-Source`
- Optional: `X-Request-Id`, `X-Transaction-Id`

## Endpoints
- POST `/v1/products`
- GET `/v1/products/{sku}`
- POST `/v1/stock/adjust`
- GET `/health`

All non-2xx responses return:
```json
{"StatusCode": 404, "StatusMessage": "Not Found", "Message": "..."}
```

## Mongo Collections
- `products`: `{ _id, sku (unique), name, price, currency, createdAt }`
- `stock`: `{ _id, sku, quantity, lastUpdated }`
- `idempotency`: `{ _id: hash(sku+delta+transactionId), sku, delta, transactionId, createdAt }`

Indexes created on startup:
- `products`: unique index on `sku`
- `idempotency`: TTL index on `createdAt` with 60 seconds

## Queries (copy/paste)
- Unique SKU insert:
```javascript
db.products.insertOne({ sku, name, price, currency, createdAt: new Date() })
```
- Get product:
```javascript
db.products.findOne({ sku })
```
- Atomic stock update:
```javascript
db.stock.updateOne(
  { sku },
  { $inc: { quantity: delta }, $set: { lastUpdated: new Date() } },
  { upsert: true }
)
```
- Idempotency flow:
```javascript
// Insert with _id = sha256(sku|delta|transactionId)
db.idempotency.insertOne({ _id: hash, sku, delta, transactionId, createdAt: new Date() })
// Duplicate key -> treat as already applied
// TTL index (60s):
db.idempotency.createIndex({ createdAt: 1 }, { expireAfterSeconds: 60 })
```

## Example cURL
```bash
# Create product
curl -sS -X POST http://localhost:8000/v1/products \
  -H 'Content-Type: application/json' \
  -H 'X-Client-Source: curl' \
  -d '{"sku":"SKU-1","name":"Mouse","price":19.99,"currency":"USD"}'

# Get product
curl -sS -H 'X-Client-Source: curl' http://localhost:8000/v1/products/SKU-1

# Adjust stock (idempotent)
curl -sS -X POST http://localhost:8000/v1/stock/adjust \
  -H 'Content-Type: application/json' -H 'X-Client-Source: curl' \
  -d '{"sku":"SKU-1","delta":5,"transactionId":"tx-1"}'

# Health
curl -sS -H 'X-Client-Source: curl' http://localhost:8000/health
```

## Tests
```bash
poetry run pytest -q
```

