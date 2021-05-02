"""Migration script for StaticDimensionRecordStorageManager 3.2.0.

Revision ID: 3859eac451aa
Revises: 36d66ca4d7a3
Create Date: 2021-05-02 17:28:13.234367

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3859eac451aa'
down_revision = '36d66ca4d7a3'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
