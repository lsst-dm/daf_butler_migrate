"""Migration script for StaticDimensionRecordStorageManager 1.2.0.

Revision ID: 2dea9d903dde
Revises: 4f4f243fea82
Create Date: 2021-05-04 16:30:37.684922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2dea9d903dde'
down_revision = '4f4f243fea82'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
