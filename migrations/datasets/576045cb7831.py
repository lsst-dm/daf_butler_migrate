"""Migration script for ByDimensionsDatasetRecordStorageManager 0.3.0.

Revision ID: 576045cb7831
Revises: 38a9414ea7a2
Create Date: 2021-05-04 16:30:50.476981

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '576045cb7831'
down_revision = '38a9414ea7a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
