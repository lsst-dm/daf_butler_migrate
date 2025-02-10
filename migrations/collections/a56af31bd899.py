"""Migration script for NameKeyCollectionManager 0.1.0.

Revision ID: a56af31bd899
Revises: 8d2e9de2f21f
Create Date: 2021-05-04 16:30:19.728318

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a56af31bd899'
down_revision = '8d2e9de2f21f'
branch_labels = ('collections-NameKeyCollectionManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
