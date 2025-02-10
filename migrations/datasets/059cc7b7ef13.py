"""This is an initial pseudo-revision of the 'datasets' tree.

Revision ID: 059cc7b7ef13
Revises:
Create Date: 2021-05-04 16:30:46.028363

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '059cc7b7ef13'
down_revision = None
branch_labels = ('datasets',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
