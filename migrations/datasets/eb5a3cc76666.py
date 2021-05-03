"""Migration script for ByDimensionsDatasetRecordStorageManager 0.1.0.

Revision ID: eb5a3cc76666
Revises: 059cc7b7ef13
Create Date: 2021-05-03 16:19:41.339100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb5a3cc76666'
down_revision = '059cc7b7ef13'
branch_labels = ('datasets-ByDimensionsDatasetRecordStorageManager',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
