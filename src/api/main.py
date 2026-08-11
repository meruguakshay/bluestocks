import json
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# Configure request logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform REST API",
    description="REST API backend exposing 16 endpoints for financial ratios, statements, screener, peers, and portfolio analytics.",
    version="1.0.0",
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Duration: {duration:.4f}s | Status: {response.status_code}"
    )
    response.headers["X-Process-Time"] = f"{duration:.4f}s"
    return response


# Startup handler to export OpenAPI spec
@app.on_event("startup")
def export_openapi_spec():
    os.makedirs("docs", exist_ok=True)
    openapi_schema = app.openapi()
    with open("docs/openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print("[OK] Saved OpenAPI spec to docs/openapi.json")


# Inclusions with prefix /api/v1
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(companies.router, prefix="/api/v1", tags=["Companies"])
app.include_router(screener.router, prefix="/api/v1", tags=["Screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["Sectors"])
app.include_router(peers.router, prefix="/api/v1", tags=["Peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["Valuation"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
