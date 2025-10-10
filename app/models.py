from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Currency(str, Enum):
	SAR = "SAR"
	USD = "USD"


class ErrorEnvelope(BaseModel):
	StatusCode: int
	StatusMessage: str
	Message: str

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"StatusCode": 404,
					"StatusMessage": "Not Found",
					"Message": "Product with sku 'ABC' not found",
				}
			]
		}
	}


class ProductCreate(BaseModel):
	sku: str = Field(..., min_length=1, max_length=128)
	name: str = Field(..., min_length=1, max_length=256)
	price: float = Field(..., ge=0)
	currency: Currency

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"sku": "SKU-123",
					"name": "Wireless Mouse",
					"price": 49.99,
					"currency": "USD",
				}
			]
		}
	}


class ProductOut(BaseModel):
	sku: str
	name: str
	price: float
	currency: Currency
	createdAt: datetime

	model_config = {
		"json_schema_extra": {
			"examples": [
				{
					"sku": "SKU-123",
					"name": "Wireless Mouse",
					"price": 49.99,
					"currency": "USD",
					"createdAt": "2025-01-01T12:00:00Z",
				}
			]
		}
	}


class StockAdjustRequest(BaseModel):
	sku: str = Field(..., min_length=1, max_length=128)
	delta: int = Field(...)
	transactionId: str = Field(..., min_length=1, max_length=128)

	model_config = {
		"json_schema_extra": {
			"examples": [
				{"sku": "SKU-123", "delta": 5, "transactionId": "tx-abc-1"}
			]
		}
	}


class StockAdjustOut(BaseModel):
	sku: str
	newQuantity: int

	model_config = {
		"json_schema_extra": {
			"examples": [
				{"sku": "SKU-123", "newQuantity": 42}
			]
		}
	}


class HealthOut(BaseModel):
	status: Literal["ok", "error"]
	timestamp: datetime
	mongodb: Literal["connected", "disconnected"]

	model_config = {
		"json_schema_extra": {
			"examples": [
				{"status": "ok", "timestamp": "2025-01-01T12:00:00Z", "mongodb": "connected"}
			]
		}
	}

