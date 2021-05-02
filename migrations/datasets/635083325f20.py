"""Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.

Revision ID: 635083325f20
Revises: 576045cb7831
Create Date: 2021-05-02 17:28:24.126532

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '635083325f20'
down_revision = '576045cb7831'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
