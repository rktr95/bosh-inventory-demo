from __future__ import annotations

import time
import logging
from typing import Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


class RequestContext:
	def __init__(self, client_id: str, correlation_id: Optional[str], transaction_id: Optional[str]):
		self.client_id = client_id
		self.correlation_id = correlation_id
		self.transaction_id = transaction_id


async def require_headers(
	x_client_source: str | None = Header(default=None, alias="X-Client-Source"),
	x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
	x_transaction_id: str | None = Header(default=None, alias="X-Transaction-Id"),
) -> RequestContext:
	if not x_client_source:
		raise HTTPException(status_code=400, detail="Missing required header: X-Client-Source")
	return RequestContext(client_id=x_client_source, correlation_id=x_request_id, transaction_id=x_transaction_id)


async def optional_headers(
	x_client_source: str | None = Header(default=None, alias="X-Client-Source", include_in_schema=False),
	x_request_id: str | None = Header(default=None, alias="X-Request-Id", include_in_schema=False),
	x_transaction_id: str | None = Header(default=None, alias="X-Transaction-Id", include_in_schema=False),
) -> RequestContext:
	"""Optional headers dependency that doesn't show in OpenAPI schema"""
	return RequestContext(client_id=x_client_source or "unknown", correlation_id=x_request_id, transaction_id=x_transaction_id)


class LoggingMiddleware:
	def __init__(self, app):
		self.app = app

	async def __call__(self, scope, receive, send):
		if scope["type"] != "http":
			return await self.app(scope, receive, send)

		method = scope.get("method")
		path = scope.get("path")
		start = time.perf_counter()
		status_code_holder = {"status": None}

		async def send_wrapper(message):
			if message.get("type") == "http.response.start":
				status_code_holder["status"] = message.get("status")
			await send(message)

		try:
			await self.app(scope, receive, send_wrapper)
		finally:
			duration_ms = int((time.perf_counter() - start) * 1000)
			headers = dict(scope.get("headers") or [])
			def _get(name: str) -> str | None:
				key = name.lower().encode()
				return headers.get(key).decode() if key in headers else None
			client_id = _get("x-client-source") or "-"
			correlation_id = _get("x-request-id") or "-"
			transaction_id = _get("x-transaction-id") or "-"
			logger.info(
				"request completed",
				extra={
					"clientId": client_id,
					"correlationId": correlation_id,
					"transactionId": transaction_id,
					"route": path,
					"method": method,
					"status": status_code_holder["status"],
					"durationMs": duration_ms,
				},
			)

