from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import logging
import traceback
import uuid

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api import router as api_router
from src.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    # ---------------------------------
    # Logging Configuration
    # ---------------------------------
    logging.basicConfig(
        level=logging.INFO if settings.ENVIRONMENT == "development" else logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

    # ---------------------------------
    # Request ID Middleware
    # ---------------------------------
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

    # ---------------------------------
    # Rate Limiting
    # ---------------------------------
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down.",
            },
        )

    # ---------------------------------
    # Request Body Size Limit (1 MB)
    # ---------------------------------
    class BodySizeLimitMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, max_body_size: int):
            super().__init__(app)
            self.max_body_size = max_body_size

        async def dispatch(self, request: Request, call_next):
            content_length = request.headers.get("content-length")

            if content_length and int(content_length) > self.max_body_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "message": "Request body too large.",
                    },
                )

            return await call_next(request)

    app.add_middleware(BodySizeLimitMiddleware, max_body_size=1_000_000)

    # ---------------------------------
    # CORS Configuration
    # ---------------------------------
    if settings.ENVIRONMENT == "development":
        allowed_origins = ["*"]
    else:
        allowed_origins = ["https://yourdomain.com"]  # Replace in production

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ---------------------------------
    # Include API Routes
    # ---------------------------------
    app.include_router(api_router)

    # ---------------------------------
    # Health Endpoint
    # ---------------------------------
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
        }

    # ---------------------------------
    # Global Exception Handler
    # ---------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")

        logging.error(f"[{request_id}] Unhandled error: {str(exc)}")
        logging.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": "internal_server_error",
                "request_id": request_id,
            },
        )

    return app


app = create_app()