"""Migration script for StaticDimensionRecordStorageManager 4.0.0.

Revision ID: e45766f0daea
Revises: 3859eac451aa
Create Date: 2021-05-04 16:30:41.803972

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e45766f0daea'
down_revision = '3859eac451aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
