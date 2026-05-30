"""
EkalavyaAI — Database Models
Complete SQLAlchemy async models for all entities.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ────────────────────────────────────────────────────────
class StudentLevel(str, enum.Enum):
    WEAK = "WEAK"
    AVERAGE = "AVERAGE"
    TOPPER = "TOPPER"


class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    INSTITUTE = "INSTITUTE"


class ExamType(str, enum.Enum):
    CA_FOUNDATION = "CA_FOUNDATION"
    CA_INTERMEDIATE = "CA_INTERMEDIATE"
    CA_FINAL = "CA_FINAL"
    JEE = "JEE"
    NEET = "NEET"


class Language(str, enum.Enum):
    ENGLISH = "English"
    BENGALI = "Bengali"
    HINDI = "Hindi"
    TAMIL = "Tamil"
    TELUGU = "Telugu"


class MistakeType(str, enum.Enum):
    CONCEPTUAL = "CONCEPTUAL"
    CALCULATION = "CALCULATION"
    CARELESS = "CARELESS"


# ── Mixins ───────────────────────────────────────────────────────
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


# ── User Models ──────────────────────────────────────────────────
class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(15))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    google_id: Mapped[Optional[str]] = mapped_column(String(100))
    plan: Mapped[str] = mapped_column(String(20), default="FREE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False)
    notes: Mapped[List["Note"]] = relationship(back_populates="student")
    credits: Mapped[Optional["Credit"]] = relationship(back_populates="student", uselist=False)
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="student")
    study_sessions: Mapped[List["StudySession"]] = relationship(back_populates="student")
    referrals_sent: Mapped[List["Referral"]] = relationship(
        back_populates="referrer", foreign_keys="Referral.referrer_id"
    )


class StudentProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    exam_targets: Mapped[List[str]] = mapped_column(JSONB, default=list)
    exam_dates: Mapped[dict] = mapped_column(JSONB, default=dict)
    level: Mapped[StudentLevel] = mapped_column(SAEnum(StudentLevel), default=StudentLevel.AVERAGE)
    language: Mapped[Language] = mapped_column(SAEnum(Language), default=Language.ENGLISH)
    weak_chapters: Mapped[List[str]] = mapped_column(JSONB, default=list)
    learning_style: Mapped[dict] = mapped_column(JSONB, default=dict)
    behavioral_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    login_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    readiness_scores: Mapped[dict] = mapped_column(JSONB, default=dict)

    user: Mapped["User"] = relationship(back_populates="profile")
    revision_schedule: Mapped[List["RevisionSchedule"]] = relationship(back_populates="student")
    mistakes: Mapped[List["Mistake"]] = relationship(back_populates="student")


# ── Exam Structure Models ────────────────────────────────────────
class Chapter(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chapters"

    exam: Mapped[ExamType] = mapped_column(SAEnum(ExamType), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    total_topics: Mapped[int] = mapped_column(Integer, default=0)
    pyq_frequency: Mapped[int] = mapped_column(Integer, default=0)

    topics: Mapped[List["Topic"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    notes: Mapped[List["Note"]] = relationship(back_populates="chapter")
    questions: Mapped[List["Question"]] = relationship(back_populates="chapter")
    master_cache: Mapped[Optional["MasterNotesCache"]] = relationship(
        back_populates="chapter", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("exam", "subject", "chapter_no", name="uq_chapter_exam_subject_no"),
        Index("ix_chapters_exam", "exam"),
    )


class Topic(Base, UUIDMixin):
    __tablename__ = "topics"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    pyq_frequency: Mapped[int] = mapped_column(Integer, default=0)

    chapter: Mapped["Chapter"] = relationship(back_populates="topics")


# ── Notes Models ─────────────────────────────────────────────────
class Note(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notes"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id")
    )
    language: Mapped[Language] = mapped_column(SAEnum(Language), nullable=False)
    content_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    docx_url: Mapped[Optional[str]] = mapped_column(String(500))
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    from_master_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    student_rating: Mapped[Optional[int]] = mapped_column(Integer)
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    agent_calls: Mapped[dict] = mapped_column(JSONB, default=dict)

    student: Mapped["User"] = relationship(back_populates="notes")
    chapter: Mapped["Chapter"] = relationship(back_populates="notes")

    __table_args__ = (
        Index("ix_notes_student_id", "student_id"),
        Index("ix_notes_chapter_id", "chapter_id"),
    )


class MasterNotesCache(Base, TimestampMixin):
    __tablename__ = "master_notes_cache"

    cache_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id"), unique=True
    )
    language: Mapped[Language] = mapped_column(SAEnum(Language))
    content_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    pdf_url: Mapped[str] = mapped_column(String(500))
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    expert_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    chapter: Mapped["Chapter"] = relationship(back_populates="master_cache")


# ── Question Models ──────────────────────────────────────────────
class Question(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "questions"

    exam: Mapped[ExamType] = mapped_column(SAEnum(ExamType))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[Optional[str]] = mapped_column(String(10))
    marks: Mapped[int] = mapped_column(Integer, default=5)
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id")
    )
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(20), default="DESCRIPTIVE")
    options: Mapped[Optional[dict]] = mapped_column(JSONB)
    correct_answer: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    examiner_notes: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    chapter: Mapped["Chapter"] = relationship(back_populates="questions")
    attempts: Mapped[List["QuestionAttempt"]] = relationship(back_populates="question")

    __table_args__ = (
        Index("ix_questions_exam_year", "exam", "year"),
        Index("ix_questions_chapter_id", "chapter_id"),
    )


class QuestionAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "question_attempts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id")
    )
    student_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[float]] = mapped_column(Float)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    question: Mapped["Question"] = relationship(back_populates="attempts")

    __table_args__ = (Index("ix_attempts_student_id", "student_id"),)


# ── Memory / Analytics Models ────────────────────────────────────
class StudySession(Base, UUIDMixin):
    __tablename__ = "study_sessions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    topics_covered: Mapped[List[str]] = mapped_column(JSONB, default=list)
    agent_calls_made: Mapped[int] = mapped_column(Integer, default=0)
    notes_generated: Mapped[int] = mapped_column(Integer, default=0)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    session_facts: Mapped[List[str]] = mapped_column(JSONB, default=list)
    memory_updated: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["User"] = relationship(back_populates="study_sessions")

    __table_args__ = (Index("ix_sessions_student_id", "student_id"),)


class Mistake(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mistakes"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.user_id", ondelete="CASCADE")
    )
    question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id")
    )
    chapter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id")
    )
    mistake_type: Mapped[MistakeType] = mapped_column(SAEnum(MistakeType))
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    student: Mapped["StudentProfile"] = relationship(back_populates="mistakes")


class RevisionSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "revision_schedule"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.user_id", ondelete="CASCADE")
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id")
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sm2_level: Mapped[int] = mapped_column(Integer, default=0)
    sm2_easiness: Mapped[float] = mapped_column(Float, default=2.5)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["StudentProfile"] = relationship(back_populates="revision_schedule")

    __table_args__ = (Index("ix_revision_student_due", "student_id", "due_date"),)


# ── Credits & Referral Models ────────────────────────────────────
class Credit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "credits"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    balance: Mapped[int] = mapped_column(Integer, default=0)
    transaction_history: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    student: Mapped["User"] = relationship(back_populates="credits")


class Referral(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "referrals"

    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    referred_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    credited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    referrer: Mapped["User"] = relationship(
        back_populates="referrals_sent", foreign_keys=[referrer_id]
    )


class Subscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payment_id: Mapped[Optional[str]] = mapped_column(String(100))
    cashfree_order_id: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    is_annual: Mapped[bool] = mapped_column(Boolean, default=False)
    amount_paid: Mapped[Optional[float]] = mapped_column(Float)

    student: Mapped["User"] = relationship(back_populates="subscriptions")

    __table_args__ = (Index("ix_subscriptions_student_id", "student_id"),)


# ── Chat Message Model ───────────────────────────────────────────
class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    session_id: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    exam: Mapped[Optional[str]] = mapped_column(String(30))
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_chat_student_session", "student_id", "session_id"),
    )
