"""Migration script for SynthIntKeyCollectionManager 1.0.0.

Revision ID: 97a6aabd8998
Revises: b4073b638219
Create Date: 2021-05-04 16:30:30.631728

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '97a6aabd8998'
down_revision = 'b4073b638219'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
