"""Migration script for ByDimensionsDatasetRecordStorageManager 0.2.0.

Revision ID: 38a9414ea7a2
Revises: eb5a3cc76666
Create Date: 2021-05-03 16:19:42.829362

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38a9414ea7a2'
down_revision = 'eb5a3cc76666'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
