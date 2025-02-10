"""Migration script for ByNameOpaqueTableStorageManager 0.1.0.

Revision ID: 61f6b63d296d
Revises: c2c46f409743
Create Date: 2021-05-04 16:30:55.896538

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '61f6b63d296d'
down_revision = 'c2c46f409743'
branch_labels = ('opaque-ByNameOpaqueTableStorageManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
