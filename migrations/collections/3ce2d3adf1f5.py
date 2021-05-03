"""Migration script for NameKeyCollectionManager 0.2.0.

Revision ID: 3ce2d3adf1f5
Revises: a56af31bd899
Create Date: 2021-05-03 16:19:12.254396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ce2d3adf1f5'
down_revision = 'a56af31bd899'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
