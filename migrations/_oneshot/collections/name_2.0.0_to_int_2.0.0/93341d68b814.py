"""Migration script for NameKeyCollectionManager 2.0.0.

This is an empty migration, it is used as a starting revision for a special
one-shot migration from NameKeyCollectionManager 2.0.0 to
SynthIntKeyCollectionManager 2.0.0.

Revision ID: 93341d68b814
Revises: 8d2e9de2f21f
Create Date: 2023-12-08 11:25:19.172876

"""
# revision identifiers, used by Alembic.
revision = "93341d68b814"
down_revision = "8d2e9de2f21f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Perform schema upgrade."""
    raise NotImplementedError()


def downgrade() -> None:
    """Perform schema downgrade."""
    raise NotImplementedError()
