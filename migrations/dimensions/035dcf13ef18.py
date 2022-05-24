"""Migration script for StaticDimensionRecordStorageManager 6.0.2.

Revision ID: 035dcf13ef18
Revises: 1601d5973bf8
Create Date: 2022-05-19 15:40:18.561744

"""
import logging

import sqlalchemy as sa
from alembic import context, op
from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes
from lsst.daf.butler_migrate.digests import get_digest
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "035dcf13ef18"
down_revision = "1601d5973bf8"
branch_labels = None
depends_on = None

_LOG = logging.getLogger(__name__)

# Manager name
MANAGER = "lsst.daf.butler.registry.dimensions.static.StaticDimensionRecordStorageManager"


def upgrade() -> None:
    """Summary of changes for this migration:

        - implied dimension columns (non-PK foreign keys) add NOT NULL

    Note that schema digests are not updated. Just before we updated code for
    6.0.2 versions we disabled validation of checksums. Older code that uses
    6.0.1 is still validating checksums so we keep checksum from 6.0.1 in the
    database.
    """
    _do_migration(nullable=False, manager_version="6.0.2")


def downgrade() -> None:
    """Reverses the effect of `upgrade`."""
    _do_migration(nullable=True, manager_version="6.0.1")


def _do_migration(nullable: bool, manager_version: str) -> None:
    """Run the whole migration.

    Parameters
    ----------
    nullable : `bool`
        False if columns are to be made NOT NULL, True if they are to be made
        NULL.
    manager_version : `str`
        Manager version to store in butler_attributes.
    """
    mig_context = context.get_context()
    bind = mig_context.bind
    schema = mig_context.version_table_schema

    inspector = Inspector.from_engine(bind)
    attributes = ButlerAttributes(bind, schema)

    # To know dimension record tables and their implied columns we need to look
    # at dimensions config.
    config = attributes.get_dimensions_json()
    for element_name, element_config in config["elements"].items():
        if (implied := element_config.get("implies")) is not None:

            # some elements do not have tables
            if not inspector.has_table(element_name, schema=schema):
                continue

            # Do it in batch in case someone wants to run it on SQLite
            with op.batch_alter_table(element_name, schema=schema) as batch_op:
                for other_element in implied:
                    # Referenced table need to exists
                    if not inspector.has_table(other_element, schema=schema):
                        continue
                    if nullable:
                        _LOG.info("Add NULL to column %s.%s", element_name, other_element)
                    else:
                        _LOG.info("Add NOT NULL to column %s.%s", element_name, other_element)
                    batch_op.alter_column(other_element, nullable=nullable)

    count = attributes.update(f"version:{MANAGER}", manager_version)
    assert count == 1, "expected to update single row"
