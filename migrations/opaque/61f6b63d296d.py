"""Migration script for ByNameOpaqueTableStorageManager 0.1.0.

Revision ID: 61f6b63d296d
Revises: c2c46f409743
Create Date: 2021-05-03 16:19:50.275843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61f6b63d296d'
down_revision = 'c2c46f409743'
branch_labels = ('opaque-ByNameOpaqueTableStorageManager',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
