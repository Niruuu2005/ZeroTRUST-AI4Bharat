"""
ZeroTRUST Verification Engine — FastAPI Main Application
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routers.verify import router as verify_router

app = FastAPI(
    title="ZeroTRUST Verification Engine",
    version="2.0.0",
    description="Multi-agent AI misinformation detection engine",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "verification-engine",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc) if os.getenv("ENVIRONMENT") != "production" else "Internal error"},
    )


app.include_router(verify_router, prefix="/verify")
