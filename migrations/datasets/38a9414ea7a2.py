"""Migration script for ByDimensionsDatasetRecordStorageManager 0.2.0.

Revision ID: 38a9414ea7a2
Revises: eb5a3cc76666
Create Date: 2021-05-04 16:30:48.982742

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '38a9414ea7a2'
down_revision = 'eb5a3cc76666'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
