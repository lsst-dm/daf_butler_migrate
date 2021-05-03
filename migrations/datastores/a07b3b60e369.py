"""Migration script for MonolithicDatastoreRegistryBridgeManager 0.2.0.

Revision ID: a07b3b60e369
Revises: bb8b5df7ff80
Create Date: 2021-05-03 16:19:56.391392

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a07b3b60e369'
down_revision = 'bb8b5df7ff80'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
