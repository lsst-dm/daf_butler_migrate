"""Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.

Revision ID: 635083325f20
Revises: 059cc7b7ef13
Create Date: 2021-05-04 16:31:04.471227

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '635083325f20'
down_revision = '059cc7b7ef13'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
