from alembic import op
import sqlalchemy as sa


revision = 'phase6_career_intelligence'
down_revision = 'bdec1b1fd5cb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'career_intelligence_memories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('career_intelligence_memories')