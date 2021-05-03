"""Migration script for NameKeyCollectionManager 2.0.0.

Revision ID: 93341d68b814
Revises: 5e75e5391603
Create Date: 2021-05-03 16:19:16.899743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93341d68b814'
down_revision = '5e75e5391603'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
