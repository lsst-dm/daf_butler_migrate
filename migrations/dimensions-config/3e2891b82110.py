"""This is an initial pseudo-revision of the 'dimensions-config' tree.

Revision ID: 3e2891b82110
Revises:
Create Date: 2022-05-13 14:37:42.026701

"""

# revision identifiers, used by Alembic.
revision = "3e2891b82110"
down_revision = None
branch_labels = ("dimensions-config",)
depends_on = None


def upgrade() -> None:
    raise NotImplementedError("No upgrades for tree root")


def downgrade() -> None:
    raise NotImplementedError("No downgrades for tree root")
