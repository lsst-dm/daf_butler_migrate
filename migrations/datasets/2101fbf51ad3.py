"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 059cc7b7ef13
Create Date: 2021-05-04 16:30:53.171818

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2101fbf51ad3'
down_revision = '059cc7b7ef13'
branch_labels = ('datasets-ByDimensionsDatasetRecordStorageManagerUUID',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
