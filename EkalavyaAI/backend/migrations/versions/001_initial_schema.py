"""Initial schema - all tables

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(15)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("google_id", sa.String(100)),
        sa.Column("plan", sa.String(20), default="FREE"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("is_admin", sa.Boolean, default=False),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Student profiles
    op.create_table(
        "student_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("exam_targets", JSONB, default=list),
        sa.Column("exam_dates", JSONB, default=dict),
        sa.Column("level", sa.String(10), default="AVERAGE"),
        sa.Column("language", sa.String(20), default="English"),
        sa.Column("weak_chapters", JSONB, default=list),
        sa.Column("learning_style", JSONB, default=dict),
        sa.Column("behavioral_profile", JSONB, default=dict),
        sa.Column("onboarding_complete", sa.Boolean, default=False),
        sa.Column("login_streak", sa.Integer, default=0),
        sa.Column("last_streak_date", sa.DateTime(timezone=True)),
        sa.Column("readiness_scores", JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Chapters
    op.create_table(
        "chapters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("exam", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("chapter_no", sa.Integer, nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("importance_score", sa.Float, default=0.5),
        sa.Column("total_topics", sa.Integer, default=0),
        sa.Column("pyq_frequency", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("exam", "subject", "chapter_no"),
    )
    op.create_index("ix_chapters_exam", "chapters", ["exam"])

    # Topics
    op.create_table(
        "topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id")),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("importance_score", sa.Float, default=0.5),
        sa.Column("pyq_frequency", sa.Integer, default=0),
    )

    # Notes
    op.create_table(
        "notes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id")),
        sa.Column("language", sa.String(20)),
        sa.Column("content_json", JSONB, default=dict),
        sa.Column("pdf_url", sa.String(500)),
        sa.Column("docx_url", sa.String(500)),
        sa.Column("quality_score", sa.Float, default=0.0),
        sa.Column("confidence_score", sa.Float, default=0.0),
        sa.Column("cached", sa.Boolean, default=False),
        sa.Column("from_master_cache", sa.Boolean, default=False),
        sa.Column("student_rating", sa.Integer),
        sa.Column("generation_time_ms", sa.Integer),
        sa.Column("agent_calls", JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notes_student_id", "notes", ["student_id"])
    op.create_index("ix_notes_chapter_id", "notes", ["chapter_id"])

    # Master notes cache
    op.create_table(
        "master_notes_cache",
        sa.Column("cache_key", sa.String(200), primary_key=True),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id"), unique=True),
        sa.Column("language", sa.String(20)),
        sa.Column("content_json", JSONB),
        sa.Column("pdf_url", sa.String(500)),
        sa.Column("quality_score", sa.Float, default=0.0),
        sa.Column("expert_verified", sa.Boolean, default=False),
        sa.Column("view_count", sa.Integer, default=0),
        sa.Column("avg_rating", sa.Float, default=0.0),
        sa.Column("rating_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Questions
    op.create_table(
        "questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("exam", sa.String(20)),
        sa.Column("year", sa.Integer),
        sa.Column("month", sa.String(10)),
        sa.Column("marks", sa.Integer),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id")),
        sa.Column("question_text", sa.Text),
        sa.Column("question_type", sa.String(20)),
        sa.Column("options", JSONB),
        sa.Column("correct_answer", sa.Text),
        sa.Column("solution", sa.Text),
        sa.Column("explanation", sa.Text),
        sa.Column("examiner_notes", sa.Text),
        sa.Column("difficulty", sa.Float, default=0.5),
        sa.Column("verified", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_questions_exam_year", "questions", ["exam", "year"])
    op.create_index("ix_questions_chapter_id", "questions", ["chapter_id"])

    # Question attempts
    op.create_table(
        "question_attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id")),
        sa.Column("student_answer", sa.Text),
        sa.Column("is_correct", sa.Boolean),
        sa.Column("ai_feedback", sa.Text),
        sa.Column("score", sa.Float),
        sa.Column("time_taken_seconds", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attempts_student_id", "question_attempts", ["student_id"])

    # Study sessions
    op.create_table(
        "study_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("topics_covered", JSONB, default=list),
        sa.Column("agent_calls_made", sa.Integer, default=0),
        sa.Column("notes_generated", sa.Integer, default=0),
        sa.Column("questions_attempted", sa.Integer, default=0),
        sa.Column("session_facts", JSONB, default=list),
        sa.Column("memory_updated", sa.Boolean, default=False),
    )
    op.create_index("ix_sessions_student_id", "study_sessions", ["student_id"])

    # Mistakes
    op.create_table(
        "mistakes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("student_profiles.user_id")),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id")),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id")),
        sa.Column("mistake_type", sa.String(20)),
        sa.Column("description", sa.Text),
        sa.Column("resolved", sa.Boolean, default=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Revision schedule
    op.create_table(
        "revision_schedule",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("student_profiles.user_id")),
        sa.Column("chapter_id", UUID(as_uuid=True), sa.ForeignKey("chapters.id")),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("sm2_level", sa.Integer, default=0),
        sa.Column("sm2_easiness", sa.Float, default=2.5),
        sa.Column("priority", sa.Integer, default=5),
        sa.Column("completed", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_revision_student_due", "revision_schedule", ["student_id", "due_date"])

    # Credits
    op.create_table(
        "credits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("balance", sa.Integer, default=0),
        sa.Column("transaction_history", JSONB, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Referrals
    op.create_table(
        "referrals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("referrer_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("referred_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("code", sa.String(20), unique=True),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("credited_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("plan", sa.String(20)),
        sa.Column("start_date", sa.DateTime(timezone=True)),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("payment_id", sa.String(100)),
        sa.Column("cashfree_order_id", sa.String(100)),
        sa.Column("status", sa.String(20), default="ACTIVE"),
        sa.Column("is_annual", sa.Boolean, default=False),
        sa.Column("amount_paid", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_student_id", "subscriptions", ["student_id"])

    # Chat messages
    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("session_id", sa.String(50)),
        sa.Column("role", sa.String(10)),
        sa.Column("content", sa.Text),
        sa.Column("exam", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_student_session", "chat_messages", ["student_id", "session_id"])


def downgrade() -> None:
    for table in ["chat_messages", "subscriptions", "referrals", "credits",
                  "revision_schedule", "mistakes", "study_sessions",
                  "question_attempts", "questions", "master_notes_cache",
                  "notes", "topics", "chapters", "student_profiles", "users"]:
        op.drop_table(table)
