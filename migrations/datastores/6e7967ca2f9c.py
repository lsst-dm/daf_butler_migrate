"""This is an initial pseudo-revision of the 'datastores' tree.

Revision ID: 6e7967ca2f9c
Revises: 
Create Date: 2021-05-03 16:19:53.235025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e7967ca2f9c'
down_revision = None
branch_labels = ('datastores',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
