"""This is an initial pseudo-revision of the 'collections' tree.

Revision ID: 8d2e9de2f21f
Revises:
Create Date: 2021-05-04 16:30:18.164583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d2e9de2f21f'
down_revision = None
branch_labels = ('collections',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
