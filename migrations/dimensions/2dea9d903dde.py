"""Migration script for StaticDimensionRecordStorageManager 1.2.0.

Revision ID: 2dea9d903dde
Revises: 4f4f243fea82
Create Date: 2021-05-04 16:30:37.684922

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2dea9d903dde'
down_revision = '4f4f243fea82'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
