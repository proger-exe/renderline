"""Add output_path to projects

Revision ID: 002
Revises: 001
Create Date: 2024-01-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("output_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "output_path")
