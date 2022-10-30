"""This is an initial pseudo-revision of the 'obscore-config' tree.

Revision ID: 2daeabfb5019
Revises:
Create Date: 2022-10-28 10:48:54.550498

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2daeabfb5019"
down_revision = None
branch_labels = ("obscore-config",)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
