"""Migration script for MonolithicDatastoreRegistryBridgeManager 0.2.1.

Revision ID: a81dddabd837
Revises: a07b3b60e369
Create Date: 2025-05-20 14:57:52.486966
"""
import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext

# revision identifiers, used by Alembic.
revision = "a81dddabd837"
down_revision = "a07b3b60e369"
branch_labels = None
depends_on = None

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")

MANAGER_NAME = "lsst.daf.butler.registry.bridge.monolithic.MonolithicDatastoreRegistryBridgeManager"
NEW_VERSION = "0.2.1"
OLD_VERSION = "0.2.0"


def upgrade() -> None:
    """Upgrade 'datastores' tree from 0.2.0 to 0.2.1 (ticket DM-50958).

    Summary of changes:

        - Order of the columns in PK of ``dataset_location_trash`` table
          is reversed.
    """
    with MigrationContext(MANAGER_NAME, NEW_VERSION) as ctx:
        # Add code to downgrade the schema using `ctx` attributes.
        _migrate(ctx, True)


def downgrade() -> None:
    """Undo changes applied in `upgrade`."""
    with MigrationContext(MANAGER_NAME, OLD_VERSION) as ctx:
        # Add code to downgrade the schema using `ctx` attributes.
        _migrate(ctx, False)


def _migrate(ctx: MigrationContext, upgrade: bool) -> None:
    """Upgrade or downgrade the schema.

    Parameters
    ----------
    ctx : `MigrationContext`
        Migration context.
    upgrade : `bool`
        Upgrade if `True`, downgrade if `False`.
    """
    pk_columns = ["dataset_id", "datastore_name"] if upgrade else ["datastore_name", "dataset_id"]
    with op.batch_alter_table("dataset_location_trash", schema=ctx.schema) as batch_op:
        # We need to recreate PK, and for Postgres we have to drop existing PK
        # first.  In sqlite we do not even have name for PK constraint, so it
        # cannot be dropped explicitly, but new one can be made anyways.
        if not ctx.is_sqlite:
            _LOG.info("Dropping existing primary key")
            batch_op.drop_constraint("dataset_location_trash_pkey")
        _LOG.info("Creating primary key with columns %s", pk_columns)
        batch_op.create_primary_key("dataset_location_trash_pkey", pk_columns)
