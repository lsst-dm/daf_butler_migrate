"""Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.

Revision ID: f1faecdf9038
Revises: be543f24dcba
Create Date: 2021-05-02 17:28:36.465807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1faecdf9038'
down_revision = 'be543f24dcba'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
