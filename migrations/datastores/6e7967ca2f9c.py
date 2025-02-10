"""This is an initial pseudo-revision of the 'datastores' tree.

Revision ID: 6e7967ca2f9c
Revises:
Create Date: 2021-05-04 16:30:58.787987

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6e7967ca2f9c'
down_revision = None
branch_labels = ('datastores',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
