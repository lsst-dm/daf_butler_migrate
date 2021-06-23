"""Migration script for StaticDimensionRecordStorageManager 0.1.0.

Revision ID: c2671338a42f
Revises: 6166dfbb5324
Create Date: 2021-05-04 16:30:34.869493

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2671338a42f'
down_revision = '6166dfbb5324'
branch_labels = ('dimensions-StaticDimensionRecordStorageManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
