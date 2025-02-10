"""Migration script for StaticDimensionRecordStorageManager 2.2.0.

Revision ID: 36d66ca4d7a3
Revises: 2dea9d903dde
Create Date: 2021-05-04 16:30:39.090992

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '36d66ca4d7a3'
down_revision = '2dea9d903dde'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
