"""Migration script for SynthIntKeyCollectionManager 0.1.0.

Revision ID: 079a1bc77f25
Revises: 8d2e9de2f21f
Create Date: 2021-05-02 17:27:59.984160

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '079a1bc77f25'
down_revision = '8d2e9de2f21f'
branch_labels = ('collections-SynthIntKeyCollectionManager',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
