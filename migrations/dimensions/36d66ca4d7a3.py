"""Migration script for StaticDimensionRecordStorageManager 2.2.0.

Revision ID: 36d66ca4d7a3
Revises: 2dea9d903dde
Create Date: 2021-05-03 16:19:32.289486

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36d66ca4d7a3'
down_revision = '2dea9d903dde'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
