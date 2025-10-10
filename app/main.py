from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.core.error_handlers import install_error_handlers
from app.core.headers import LoggingMiddleware, RequestContext, require_headers, optional_headers
from app.db import close_mongo_connection, connect_to_mongo
from app.models import HealthOut
from app.api.routers import products as products_router
from app.api.routers import stock as stock_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Inventory Service", version="0.1.0")
app.add_middleware(LoggingMiddleware)

install_error_handlers(app)


@app.on_event("startup")
async def on_startup():
	await connect_to_mongo()


@app.on_event("shutdown")
async def on_shutdown():
	await close_mongo_connection()


app.include_router(products_router.router)
app.include_router(stock_router.router)


@app.get("/health", response_model=HealthOut, tags=["health"]) 
async def health(_ctx: RequestContext = Depends(optional_headers)):
	from app.db import get_database
	
	try:
		# Test MongoDB connection
		db = get_database()
		await db.command("ping")
		mongodb_status = "connected"
		status = "ok"
	except Exception:
		mongodb_status = "disconnected"
		status = "error"
	
	return HealthOut(
		status=status, 
		timestamp=datetime.now(timezone.utc),
		mongodb=mongodb_status
	)

