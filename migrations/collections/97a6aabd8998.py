"""Migration script for SynthIntKeyCollectionManager 1.0.0.

Revision ID: 97a6aabd8998
Revises: b4073b638219
Create Date: 2021-05-02 17:28:03.951376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97a6aabd8998'
down_revision = 'b4073b638219'
branch_labels = None
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
