"""Migration script for SynthIntKeyCollectionManager 0.3.0.

Revision ID: b4073b638219
Revises: 1a93ca89bc27
Create Date: 2021-05-04 16:30:29.269649

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b4073b638219'
down_revision = '1a93ca89bc27'
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
