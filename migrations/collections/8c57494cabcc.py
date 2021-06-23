"""Migration script for SynthIntKeyCollectionManager 2.0.0.

Revision ID: 8c57494cabcc
Revises: 97a6aabd8998
Create Date: 2021-05-04 16:30:32.047817

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c57494cabcc'
down_revision = '97a6aabd8998'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
