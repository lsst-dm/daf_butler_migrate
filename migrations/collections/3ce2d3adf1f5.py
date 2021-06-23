"""Migration script for NameKeyCollectionManager 0.2.0.

Revision ID: 3ce2d3adf1f5
Revises: a56af31bd899
Create Date: 2021-05-04 16:30:21.199073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ce2d3adf1f5'
down_revision = 'a56af31bd899'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
