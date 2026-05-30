"""
EkalavyaAI — Backend Configuration
Centralized settings management using Pydantic BaseSettings.
"""
import json
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "EkalavyaAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── AI Model APIs ────────────────────────────────────────────
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GOOGLE_AI_STUDIO_API_KEY: str = "AIza_placeholder"
    NVIDIA_NIM_API_KEY: Optional[str] = None
    COHERE_API_KEY: str = "cohere_placeholder"
    ANTHROPIC_API_KEY: Optional[str] = None

    # ── AI Model Names ───────────────────────────────────────────
    TEACHER_MODEL_PRIMARY: str = "anthropic/claude-sonnet-4-5"
    TEACHER_MODEL_BACKUP1: str = "openai/gpt-4o"
    TEACHER_MODEL_BACKUP2: str = "google/gemini-pro-1.5"
    TEACHER_MODEL_FREE: str = "llama-3.1-70b-versatile"
    SYLLABUS_MODEL_PRIMARY: str = "google/gemini-pro-1.5"
    SYLLABUS_MODEL_BACKUP1: str = "anthropic/claude-sonnet-4-5"
    SYLLABUS_MODEL_BACKUP2: str = "openai/gpt-4o"
    SYLLABUS_MODEL_FREE: str = "llama-3.1-70b-versatile"
    RESEARCH_MODEL_PRIMARY: str = "openai/gpt-4o"
    RESEARCH_MODEL_BACKUP1: str = "deepseek/deepseek-chat"
    RESEARCH_MODEL_FREE: str = "llama-3.1-70b-versatile"
    PYQ_MODEL_PRIMARY: str = "openai/gpt-4o"
    PYQ_MODEL_BACKUP1: str = "openai/gpt-4o-mini"
    PYQ_MODEL_FREE: str = "mixtral-8x7b-32768"
    NOTES_MODEL_PRIMARY: str = "anthropic/claude-sonnet-4-5"
    DIAGRAM_MODEL_PRIMARY: str = "anthropic/claude-sonnet-4-5"
    MEMORY_MODEL: str = "llama-3.1-70b-versatile"
    MEMORY_MODEL_BACKUP: str = "gemma2-9b-it"
    GENERAL_CHAT_MODEL: str = "llama-3.1-8b-instant"

    # ── Databases ────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ekalavya:ekalavya_dev_pass@localhost:5432/ekalavya"
    REDIS_URL: str = "redis://localhost:6379/0"
    PINECONE_API_KEY: str = "pinecone_placeholder"
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "ekalavya-knowledge"
    PINECONE_MEMORY_INDEX: str = "ekalavya-memory"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "ekalavya-chunks"

    # ── Auth ─────────────────────────────────────────────────────
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_KEY: str = "supabase_key_placeholder"
    JWT_SECRET_KEY: str = "change-this-to-a-random-32-plus-character-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # ── Storage ──────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = "aws_key_placeholder"
    AWS_SECRET_ACCESS_KEY: str = "aws_secret_placeholder"
    AWS_S3_BUCKET: str = "ekalavya-notes"
    AWS_REGION: str = "ap-south-1"
    CLOUDFLARE_R2_ENDPOINT: Optional[str] = None
    CLOUDFLARE_R2_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_R2_SECRET_KEY: Optional[str] = None
    USE_R2: bool = False

    # ── Payment ──────────────────────────────────────────────────
    CASHFREE_APP_ID: str = "cashfree_app_id"
    CASHFREE_SECRET_KEY: str = "cashfree_secret"
    CASHFREE_ENV: str = "TEST"

    # ── Email ────────────────────────────────────────────────────
    RESEND_API_KEY: str = "re_placeholder"
    FROM_EMAIL: str = "noreply@ekalavya.ai"
    FROM_NAME: str = "EkalavyaAI"

    # ── Monitoring ───────────────────────────────────────────────
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "ekalavya-ai"
    SENTRY_DSN: Optional[str] = None

    # ── RAG Config ───────────────────────────────────────────────
    EMBEDDING_MODEL: str = "voyage-2"
    EMBEDDING_DIMENSION: int = 1024
    RAG_TOP_K_VECTOR: int = 20
    RAG_TOP_K_BM25: int = 20
    RAG_FINAL_TOP_K: int = 8
    CHUNK_SIZE_DEFAULT: int = 500
    CHUNK_OVERLAP: int = 50

    # ── Cache ────────────────────────────────────────────────────
    NOTES_CACHE_TTL_SECONDS: int = 86400 * 30
    MASTER_CACHE_PREFIX: str = "notes:master:"
    SESSION_CACHE_PREFIX: str = "session:"

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_FREE_PER_MINUTE: int = 10
    RATE_LIMIT_BASIC_PER_MINUTE: int = 30
    RATE_LIMIT_PRO_PER_MINUTE: int = 100

    # ── Agent Timeouts ───────────────────────────────────────────
    AGENT_TIMEOUT_SECONDS: int = 30
    PDF_GENERATION_TIMEOUT: int = 60
    STREAM_TIMEOUT_SECONDS: int = 120

    # ── Anti-Hallucination ───────────────────────────────────────
    CONFIDENCE_THRESHOLD: float = 0.75

    @field_validator("DATABASE_URL")
    @classmethod
    def ensure_async_db(cls, v: str) -> str:
        if "postgresql://" in v and "asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @model_validator(mode="after")
    def warn_placeholder_keys(self):
        if self.ENVIRONMENT == "production":
            if "placeholder" in self.JWT_SECRET_KEY:
                raise ValueError("JWT_SECRET_KEY must be set in production")
            if "placeholder" in self.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY must be set in production")
        return self

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# ── Module-level constants (not inside Settings) ─────────────────
SUPPORTED_EXAMS = ["CA_FOUNDATION", "CA_INTERMEDIATE", "CA_FINAL", "JEE", "NEET"]

EXAM_SUBJECTS = {
    "CA_FOUNDATION": [
        "Principles and Practice of Accounting", "Business Mathematics",
        "Logical Reasoning and Statistics", "Business Economics",
        "Business and Commercial Knowledge",
    ],
    "CA_INTERMEDIATE": [
        "Advanced Accounting", "Corporate Laws",
        "Cost and Management Accounting", "Taxation",
        "Auditing and Code of Ethics", "Financial Management and Economics",
    ],
    "CA_FINAL": [
        "Financial Reporting", "Strategic Financial Management",
        "Advanced Auditing", "Corporate Laws",
        "Strategic Cost Management", "Direct Tax Laws", "Indirect Tax Laws",
    ],
    "JEE": ["Physics", "Chemistry", "Mathematics"],
    "NEET": ["Physics", "Chemistry", "Biology"],
}

STUDENT_LEVELS = ["WEAK", "AVERAGE", "TOPPER"]
SUPPORTED_LANGUAGES = ["English", "Bengali", "Hindi", "Tamil", "Telugu"]

# SM-2 Spaced Repetition intervals (days)
SM2_INTERVALS = [1, 3, 7, 14, 30, 60]

SUBSCRIPTION_PLANS = {
    "FREE": {
        "price_monthly": 0,
        "general_chat_per_day": 10,
        "chapter_explanations_per_month": 3,
        "pyq_questions": 5,
        "notes_download_per_month": 0,
        "exams": 1,
        "languages": ["English"],
    },
    "BASIC": {
        "price_monthly": 299,
        "price_annual": 2499,
        "general_chat_per_day": -1,
        "chapter_explanations_per_month": 15,
        "pyq_questions": -1,
        "notes_download_per_month": 10,
        "exams": 1,
        "languages": ["English", "Bengali"],
    },
    "PRO": {
        "price_monthly": 599,
        "price_annual": 4999,
        "general_chat_per_day": -1,
        "chapter_explanations_per_month": -1,
        "pyq_questions": -1,
        "notes_download_per_month": -1,
        "notes_docx": True,
        "exams": 5,
        "languages": ["English", "Bengali", "Hindi", "Tamil", "Telugu"],
        "memory_system": "full",
        "weekly_study_plan": True,
        "readiness_score": True,
    },
    "INSTITUTE": {
        "price_monthly": 4999,
        "price_annual": 44999,
        "student_accounts": 30,
        "teacher_dashboard": True,
        "all_features": True,
    },
}

CREDIT_ACTIONS = {
    "REFERRAL_SUCCESS": 200,
    "REFERRAL_BONUS_NEW_USER": 100,
    "SEVEN_DAY_STREAK": 50,
    "NOTES_RATING": 10,
    "PYQ_COMPLETE_10": 20,
    "COMPLETE_PROFILE": 30,
    "BUG_REPORT": 100,
    "SHARE_NOTES": 20,
}

CREDIT_REDEMPTIONS = {
    "EXTRA_NOTES_PDF": 150,
    "ONE_WEEK_PRO_EXTENSION": 500,
    "LANGUAGE_PACK_UNLOCK": 200,
    "ONE_MONTH_BASIC_FREE": 1500,
}
