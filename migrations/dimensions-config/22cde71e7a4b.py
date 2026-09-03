"""Migration script to fix a bug in daf_butler visit table introduced in the
migration script for daf_butler universe 5 to 6.  Adds a missing index on the
day_obs column for the visit table.

Revision ID: 22cde71e7a4b
Revises: aa7a2f893cba
Create Date: 2026-09-01 15:41:19.623630

"""
import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext

# revision identifiers, used by Alembic.
revision = "22cde71e7a4b"
down_revision = "aa7a2f893cba"
branch_labels = None
depends_on = None

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")

_FOREIGN_KEY_NAME = "fkey_visit_day_obs_instrument_id_instrument_day_obs"
_TABLE_NAME = "visit"

def upgrade() -> None:
    """Apply a bug fix for the universe 5 -> 6 migration on top of daf_butler
    universe 9.

    Summary of changes:
      - Add day_obs foreign key constraint to visit table.
      - Add day_obs index to visit table.
    """
    ctx = MigrationContext()

    if _already_has_foreign_key(ctx):
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
    """Downgrading does nothing.  Repos created from scratch with dimension
    universe 6 or later already have the changes from this migration.  The
    migration for dimension universe 6 does not support downgrade, so there
    will never be a case where these indexes should be removed by migration.
    """
    pass

def _already_has_foreign_key(ctx: MigrationContext) -> bool:
    existing_fkeys = sa.inspect(ctx.bind).get_foreign_keys(_TABLE_NAME)
    return any(fk['name'] == _FOREIGN_KEY_NAME for fk in existing_fkeys)