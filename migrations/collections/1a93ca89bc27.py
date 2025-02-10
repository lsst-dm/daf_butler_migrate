"""Migration script for SynthIntKeyCollectionManager 0.2.0.

Revision ID: 1a93ca89bc27
Revises: 079a1bc77f25
Create Date: 2021-05-04 16:30:27.981554

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1a93ca89bc27'
down_revision = '079a1bc77f25'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
