"""Add Job and Application AI metadata fields

Revision ID: 1c2b3a4d5e6f
Revises: 52d336636578
Create Date: 2026-07-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1c2b3a4d5e6f"
down_revision: Union[str, None] = "52d336636578"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("ai_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("ats_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("hidden_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("interview_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("missing_certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("red_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("extracted_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "applications",
        sa.Column("match_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("gap_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("learning_recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("estimated_match_after_learning", sa.Float(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("recruiter_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("applications", "recruiter_notes")
    op.drop_column("applications", "estimated_match_after_learning")
    op.drop_column("applications", "learning_recommendations")
    op.drop_column("applications", "missing_skills")
    op.drop_column("applications", "strengths")
    op.drop_column("applications", "gap_analysis")
    op.drop_column("applications", "match_score")

    op.drop_column("jobs", "embedding")
    op.drop_column("jobs", "extracted_keywords")
    op.drop_column("jobs", "red_flags")
    op.drop_column("jobs", "missing_certifications")
    op.drop_column("jobs", "interview_focus")
    op.drop_column("jobs", "hidden_requirements")
    op.drop_column("jobs", "ats_keywords")
    op.drop_column("jobs", "ai_summary")