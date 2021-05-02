"""Migration script for NameKeyCollectionManager 0.1.0.

Revision ID: a56af31bd899
Revises: 8d2e9de2f21f
Create Date: 2021-05-02 17:27:53.504309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a56af31bd899'
down_revision = '8d2e9de2f21f'
branch_labels = ('collections-NameKeyCollectionManager',)
depends_on = None


def upgrade():
    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()
