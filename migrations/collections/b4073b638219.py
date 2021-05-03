"""Migration script for SynthIntKeyCollectionManager 0.3.0.

Revision ID: b4073b638219
Revises: 1a93ca89bc27
Create Date: 2021-05-03 16:19:21.499489

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
