"""Migration script for StaticDimensionRecordStorageManager 0.2.0.

Revision ID: 4f4f243fea82
Revises: c2671338a42f
Create Date: 2021-05-04 16:30:36.257007

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4f4f243fea82'
down_revision = 'c2671338a42f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
