"""
EkalavyaAI — FastAPI Application Entry Point
India's first AI Education Operating System
"""
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from config import settings
from api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from api.routes import auth, notes, chat, practice, progress, student, admin, payments
from models.database import create_tables
from utils.logger import setup_logging

# ─── Logging ────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ─── Sentry (Production) ────────────────────────────────────────────────────
if settings.SENTRY_DSN and settings.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )


# ─── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create database tables
    await create_tables()
    logger.info("✅ Database tables ready")

    # Initialize Pinecone
    from rag.embeddings import init_pinecone
    await init_pinecone()
    logger.info("✅ Pinecone initialized")

    # Initialize LangSmith tracing
    if settings.LANGSMITH_API_KEY:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        logger.info("✅ LangSmith tracing enabled")

    logger.info("✅ EkalavyaAI is LIVE — Learn Like a Topper!")
    yield

    logger.info("⏹ Shutting down EkalavyaAI...")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EkalavyaAI API",
    description="""
    ## EkalavyaAI — India's first AI Education Operating System

    Multi-agent AI platform for CA Foundation, CA Intermediate, CA Final, JEE & NEET students.

    ### Key Features
    - 🤖 **7 Specialized AI Agents** — powered by Claude 3.5 Sonnet, GPT-4o, Gemini
    - 📝 **Premium Notes Generation** — handwriting-style PDF with exam-quality content
    - 🎯 **PYQ Practice** — 10 years of past year questions with AI feedback
    - 🧠 **Student Memory** — long-term personalization via Pinecone
    - 🛡️ **Anti-Hallucination** — 5-layer protection system
    - 🌍 **Multi-language** — English, Bengali, Hindi, Tamil, Telugu
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ─── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["Authentication"])
app.include_router(notes.router, prefix=f"{PREFIX}/notes", tags=["Notes"])
app.include_router(chat.router, prefix=f"{PREFIX}/chat", tags=["Chat"])
app.include_router(practice.router, prefix=f"{PREFIX}/practice", tags=["Practice"])
app.include_router(progress.router, prefix=f"{PREFIX}/progress", tags=["Progress"])
app.include_router(student.router, prefix=f"{PREFIX}/student", tags=["Student"])
app.include_router(admin.router, prefix=f"{PREFIX}/admin", tags=["Admin"])
app.include_router(payments.router, prefix=f"{PREFIX}/payments", tags=["Payments"])


# ─── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Platform health check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "EkalavyaAI API — Learn Like a Topper",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }


# ─── Exception Handlers ──────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Our team has been notified."},
    )
