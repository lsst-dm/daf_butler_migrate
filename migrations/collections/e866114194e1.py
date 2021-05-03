"""Migration script for NameKeyCollectionManager 0.3.0.

Revision ID: e866114194e1
Revises: 3ce2d3adf1f5
Create Date: 2021-05-03 16:19:13.799024

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e866114194e1'
down_revision = '3ce2d3adf1f5'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
