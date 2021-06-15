"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 576045cb7831
Create Date: 2021-05-04 16:31:10.006400

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2101fbf51ad3'
down_revision = '576045cb7831'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
