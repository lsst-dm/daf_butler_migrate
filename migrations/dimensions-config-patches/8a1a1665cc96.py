"""This is an initial pseudo-revision of the 'dimensions-config-patches' tree.

Revision ID: 8a1a1665cc96
Revises:
Create Date: 2026-09-12 14:26:21.599357
"""

# revision identifiers, used by Alembic.
revision = "8a1a1665cc96"
down_revision = None
branch_labels = ("dimensions-config-patches",)
depends_on = None

TREE_NAME = "dimensions-config-patches"


def upgrade() -> None:
    """Create alembic entry, this empty migration is equivalent to executing
    `stamp` command.
    """
    pass


def downgrade() -> None:
    raise NotImplementedError()
