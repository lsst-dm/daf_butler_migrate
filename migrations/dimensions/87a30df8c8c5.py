"""Migration script for StaticDimensionRecordStorageManager 6.0.0.

Revision ID: 87a30df8c8c5
Revises: a1e0fefed6c7
Create Date: 2021-05-02 17:28:17.266960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87a30df8c8c5'
down_revision = 'a1e0fefed6c7'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
