"""Migration script for NameKeyCollectionManager 2.0.0.

Revision ID: 93341d68b814
Revises: 5e75e5391603
Create Date: 2021-05-04 16:30:25.367976

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '93341d68b814'
down_revision = '5e75e5391603'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
