"""Migration script for StaticDimensionRecordStorageManager 5.0.0.

Revision ID: a1e0fefed6c7
Revises: e45766f0daea
Create Date: 2021-05-04 16:30:43.209645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1e0fefed6c7'
down_revision = 'e45766f0daea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
