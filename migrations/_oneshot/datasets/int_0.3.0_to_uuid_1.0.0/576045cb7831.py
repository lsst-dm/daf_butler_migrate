"""Migration script for ByDimensionsDatasetRecordStorageManager 0.3.0.

Revision ID: 576045cb7831
Revises: 059cc7b7ef13
Create Date: 2021-05-04 16:31:08.617724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '576045cb7831'
down_revision = '059cc7b7ef13'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
