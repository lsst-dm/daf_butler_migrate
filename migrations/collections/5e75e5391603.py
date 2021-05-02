"""Migration script for NameKeyCollectionManager 1.0.0.

Revision ID: 5e75e5391603
Revises: e866114194e1
Create Date: 2021-05-02 17:27:57.409682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e75e5391603'
down_revision = 'e866114194e1'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
