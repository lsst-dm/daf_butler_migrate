"""This is an initial pseudo-revision of the 'opaque' tree.

Revision ID: c2c46f409743
Revises: 
Create Date: 2021-05-04 16:30:54.602018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2c46f409743'
down_revision = None
branch_labels = ('opaque',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
