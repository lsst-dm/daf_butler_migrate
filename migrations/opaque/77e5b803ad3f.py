"""Migration script for ByNameOpaqueTableStorageManager 0.2.0.

Revision ID: 77e5b803ad3f
Revises: 61f6b63d296d
Create Date: 2021-05-02 17:28:29.576509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77e5b803ad3f'
down_revision = '61f6b63d296d'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
