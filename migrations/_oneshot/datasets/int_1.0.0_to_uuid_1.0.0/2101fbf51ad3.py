"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 635083325f20
Create Date: 2021-05-04 16:31:05.926989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2101fbf51ad3'
down_revision = '635083325f20'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
