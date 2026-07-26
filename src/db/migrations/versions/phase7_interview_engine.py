from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'phase7_interview_engine'
down_revision = 'b6d101cb675e'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _has_column('interview_sessions', 'interview_type'):
        op.add_column('interview_sessions', sa.Column('interview_type', sa.String(), nullable=True))
    if not _has_column('interview_sessions', 'target_role'):
        op.add_column('interview_sessions', sa.Column('target_role', sa.String(), nullable=True))
    if not _has_column('interview_sessions', 'target_company'):
        op.add_column('interview_sessions', sa.Column('target_company', sa.String(), nullable=True))
    if not _has_column('interview_sessions', 'difficulty'):
        op.add_column('interview_sessions', sa.Column('difficulty', sa.String(), nullable=True))
    if not _has_column('interview_sessions', 'duration_seconds'):
        op.add_column('interview_sessions', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    if not _has_column('interview_sessions', 'questions'):
        op.add_column('interview_sessions', sa.Column('questions', sa.dialects.postgresql.JSONB(), nullable=True))
    if not _has_column('interview_sessions', 'overall_score'):
        op.add_column('interview_sessions', sa.Column('overall_score', sa.Float(), nullable=True))
    if not _has_column('interview_sessions', 'feedback_summary'):
        op.add_column('interview_sessions', sa.Column('feedback_summary', sa.dialects.postgresql.JSONB(), nullable=True))


def downgrade():
    for column_name in ['feedback_summary', 'overall_score', 'questions', 'duration_seconds', 'difficulty', 'target_company', 'target_role', 'interview_type']:
        if _has_column('interview_sessions', column_name):
            op.drop_column('interview_sessions', column_name)
