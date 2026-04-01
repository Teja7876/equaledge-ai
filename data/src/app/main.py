from typing import Optional
import logging

from fastapi import FastAPI, Depends, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.security import verify_api_key
from app.services.answer_service import generate_answer


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("equaledge")


# ---------------------------------------------------
# Rate Limiter Configuration (Proxy Safe)
# ---------------------------------------------------

def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


limiter = Limiter(key_func=client_ip)


# ---------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------

app = FastAPI(
    title="Disability Master AI",
    description="Strict Grounded Legal AI Engine for RPwD Act 2016",
    version="3.0"
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# ---------------------------------------------------
# CORS Configuration
# ---------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# Custom Rate Limit Handler
# ---------------------------------------------------

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please slow down."
        }
    )


# ---------------------------------------------------
# Request Schema
# ---------------------------------------------------

class QueryRequest(BaseModel):

    q: str = Field(..., min_length=2, description="User legal question")
    mode: Optional[str] = Field(
        default="retrieval",
        description="retrieval | qa | reasoning"
    )


# ---------------------------------------------------
# API Router
# ---------------------------------------------------

router = APIRouter(prefix="/api/v1", tags=["Legal AI"])


# ---------------------------------------------------
# Health Endpoint
# ---------------------------------------------------

@app.get("/health", tags=["System"])
async def health():

    return {
        "status": "running",
        "engine": "Disability Master AI",
        "mode_support": ["retrieval", "qa", "reasoning"]
    }


# ---------------------------------------------------
# Query Endpoint
# ---------------------------------------------------

@router.post("/query")
@limiter.limit("30/minute")
async def query(
    request: Request,
    payload: QueryRequest,
    api_key: str = Depends(verify_api_key)
):

    """
    Modes:
        retrieval  → deterministic legal output
        qa         → grounded explanation
        reasoning  → structured reasoning
    """

    mode = (payload.mode or "retrieval").lower()

    if mode not in {"retrieval", "qa", "reasoning"}:
        mode = "retrieval"

    try:

        logger.info(f"Query received | mode={mode}")

        result = generate_answer(payload.q, mode=mode)

        return JSONResponse(content=result)

    except Exception:

        logger.exception("Query processing failed")

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error"
            }
        )


# ---------------------------------------------------
# Register Router
# ---------------------------------------------------

app.include_router(router)
