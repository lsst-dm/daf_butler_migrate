"""Migration script for SynthIntKeyCollectionManager 0.3.0.

Revision ID: b4073b638219
Revises: 1a93ca89bc27
Create Date: 2021-05-02 17:28:02.645246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4073b638219'
down_revision = '1a93ca89bc27'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
