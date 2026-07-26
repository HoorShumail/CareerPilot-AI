"""add source description to resume versions

Revision ID: 52d336636578
Revises: eba2dae3f6ff
Create Date: 2026-07-18 13:41:34.536372

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "52d336636578"
down_revision: Union[str, None] = "eba2dae3f6ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resume_versions",
        sa.Column("source_description", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column(
        "resume_versions",
        "source_description",
    )