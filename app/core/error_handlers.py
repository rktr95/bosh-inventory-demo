from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import ErrorEnvelope

logger = logging.getLogger(__name__)


_STATUS_TEXT = {
	400: "Bad Request",
	401: "Unauthorized",
	403: "Forbidden",
	404: "Not Found",
	409: "Conflict",
	422: "Unprocessable Entity",
	500: "Internal Server Error",
}


def _envelope(status_code: int, message: str) -> ErrorEnvelope:
	return ErrorEnvelope(
		StatusCode=status_code,
		StatusMessage=_STATUS_TEXT.get(status_code, "Error"),
		Message=message,
	)


def install_error_handlers(app: FastAPI) -> None:
	@app.exception_handler(HTTPException)
	async def http_exception_handler(_: Request, exc: HTTPException):
		payload = _envelope(exc.status_code, exc.detail if exc.detail else _STATUS_TEXT.get(exc.status_code, "Error"))
		return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

	@app.exception_handler(RequestValidationError)
	async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
		payload = _envelope(422, "Validation failed")
		return JSONResponse(status_code=422, content=payload.model_dump())

	@app.exception_handler(ValidationError)
	async def pydantic_validation_exception_handler(_: Request, exc: ValidationError):
		payload = _envelope(422, "Validation failed")
		return JSONResponse(status_code=422, content=payload.model_dump())

	@app.exception_handler(Exception)
	async def unhandled_exception_handler(request: Request, exc: Exception):
		logger.exception("Unhandled exception: %s", exc)
		payload = _envelope(500, "Internal Server Error")
		return JSONResponse(status_code=500, content=payload.model_dump())

