"""Migration script for DefaultButlerAttributeManager 1.0.0.

Revision ID: f22a777cf382
Revises: f0a3531f97ca
Create Date: 2021-05-04 16:30:16.571429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f22a777cf382'
down_revision = 'f0a3531f97ca'
branch_labels = ('attributes-DefaultButlerAttributeManager',)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError()


def downgrade() -> None:
    raise NotImplementedError()
