"""Migration script for MonolithicDatastoreRegistryBridgeManager 0.1.0.

Revision ID: bb8b5df7ff80
Revises: 6e7967ca2f9c
Create Date: 2021-05-03 16:19:54.819896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb8b5df7ff80'
down_revision = '6e7967ca2f9c'
branch_labels = ('datastores-MonolithicDatastoreRegistryBridgeManager',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
