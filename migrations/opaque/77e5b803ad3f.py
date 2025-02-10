"""Migration script for ByNameOpaqueTableStorageManager 0.2.0.

Revision ID: 77e5b803ad3f
Revises: 61f6b63d296d
Create Date: 2021-05-04 16:30:57.345621

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '77e5b803ad3f'
down_revision = '61f6b63d296d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
