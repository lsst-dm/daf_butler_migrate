"""This is an initial pseudo-revision of the 'obscore' tree.

Revision ID: 8b8e030aba2b
Revises:
Create Date: 2022-10-27 16:03:57.771563

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8b8e030aba2b"
down_revision = None
branch_labels = ("obscore",)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
