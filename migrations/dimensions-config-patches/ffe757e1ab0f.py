"""Patch script for dimensions.yaml, namespace=daf_butler version=v6-patch1.

Revision ID: ffe757e1ab0f
Revises: 8a1a1665cc96
Create Date: 2026-09-12 14:26:23.462846
"""
import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext

# revision identifiers, used by Alembic.
revision = "ffe757e1ab0f"
down_revision = "8a1a1665cc96"
branch_labels = ("dimensions-config-patches-daf_butler",)
# This migration patches universe v6, should be run only after that migration.
depends_on = ("1fae088c80b6",)

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")

TREE_NAME = "dimensions-config-patches"
MANAGER_NAME = "daf_butler"
NEW_VERSION = "v6-patch1"


_FOREIGN_KEY_NAME = "fkey_visit_day_obs_instrument_id_instrument_day_obs"
_TABLE_NAME = "visit"


def upgrade() -> None:
    """Upgrade 'dimensions-config-patches' tree to daf_butler/v6-patch1 (ticket
    DM-55966). Applies a bug fix for the universe 5 -> 6 migration.

    Summary of changes:
      - Add day_obs foreign key constraint to visit table.
      - Add day_obs index to visit table.
    """
    with MigrationContext(MANAGER_NAME, NEW_VERSION, patch=True, tree_name=TREE_NAME) as ctx:

        existing_fkeys = sa.inspect(ctx.bind).get_foreign_keys(_TABLE_NAME, schema=ctx.schema)
        fk_exists = any(fk["name"] == _FOREIGN_KEY_NAME for fk in existing_fkeys)

        if fk_exists:
            _LOG.info("visit.day_obs foreign key already exists, no work to do.")
        else:
            _LOG.info("Updating visit table to add foreign key for day_obs table")
            with op.batch_alter_table(_TABLE_NAME, schema=ctx.schema) as batch_op:
                batch_op.alter_column("day_obs", nullable=False)
                batch_op.create_foreign_key(
                    constraint_name=_FOREIGN_KEY_NAME,
                    referent_table="day_obs",
                    local_cols=["instrument", "day_obs"],
                    remote_cols=["instrument", "id"],
                    referent_schema=ctx.schema,
                )

            _LOG.info("Creating index on visit.day_obs")
            op.create_index(
                "visit_fkidx_instrument_day_obs",
                _TABLE_NAME,
                ["instrument", "day_obs"],
                schema=ctx.schema,
                if_not_exists=True
            )


def downgrade() -> None:
    """Undo changes done in `upgrade`."""
    # This is the very first migration in the tree, currently the is no way
    # to restore the state of butler_attributes and we do not really want to
    # undo this migration in any case.
    raise NotImplementedError()
