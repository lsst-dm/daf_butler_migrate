"""Migration script for StaticDimensionRecordStorageManager 3.2.0.

Revision ID: 3859eac451aa
Revises: 36d66ca4d7a3
Create Date: 2021-05-04 16:30:40.488941

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3859eac451aa'
down_revision = '36d66ca4d7a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
