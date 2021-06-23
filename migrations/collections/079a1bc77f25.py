"""Migration script for SynthIntKeyCollectionManager 0.1.0.

Revision ID: 079a1bc77f25
Revises: 8d2e9de2f21f
Create Date: 2021-05-04 16:30:26.623802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '079a1bc77f25'
down_revision = '8d2e9de2f21f'
branch_labels = ('collections-SynthIntKeyCollectionManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
