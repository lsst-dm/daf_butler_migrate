"""Migration script for NameKeyCollectionManager 1.0.0.

Revision ID: 5e75e5391603
Revises: e866114194e1
Create Date: 2021-05-04 16:30:23.980922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e75e5391603'
down_revision = 'e866114194e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
