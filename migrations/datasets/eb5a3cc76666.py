"""Migration script for ByDimensionsDatasetRecordStorageManager 0.1.0.

Revision ID: eb5a3cc76666
Revises: 059cc7b7ef13
Create Date: 2021-05-04 16:30:47.418654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb5a3cc76666'
down_revision = '059cc7b7ef13'
branch_labels = ('datasets-ByDimensionsDatasetRecordStorageManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
