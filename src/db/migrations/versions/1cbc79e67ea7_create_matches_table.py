"""create matches table

Revision ID: 1cbc79e67ea7
Revises: 1c2b3a4d5e6f
Create Date: 2026-07-21 19:58:38.080809

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1cbc79e67ea7"
down_revision: Union[str, None] = "1c2b3a4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("resume_version_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("overall_match_score", sa.Float(), nullable=True),
        sa.Column("ats_score", sa.Float(), nullable=True),
        sa.Column("matched_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_technologies", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("experience_gap", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("education_gap", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("strength_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("weakness_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("priority_learning_roadmap", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resume_improvements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("estimated_match_after_learning", sa.Float(), nullable=True),
        sa.Column("interview_preparation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("final_recommendation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["resume_version_id"], ["resume_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("matches")