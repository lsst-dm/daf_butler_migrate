"""Migration script for SynthIntKeyCollectionManager 0.2.0.

Revision ID: 1a93ca89bc27
Revises: 079a1bc77f25
Create Date: 2021-05-04 16:30:27.981554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a93ca89bc27'
down_revision = '079a1bc77f25'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
