"""Migration script for MonolithicDatastoreRegistryBridgeManager 0.2.0.

Revision ID: a07b3b60e369
Revises: bb8b5df7ff80
Create Date: 2021-05-04 16:31:01.640821

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a07b3b60e369'
down_revision = 'bb8b5df7ff80'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
