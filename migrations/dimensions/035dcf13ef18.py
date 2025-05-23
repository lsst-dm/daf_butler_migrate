"""Migration script for StaticDimensionRecordStorageManager 6.0.2.

Revision ID: 035dcf13ef18
Revises: 1601d5973bf8
Create Date: 2022-05-19 15:40:18.561744

"""
import logging
from typing import cast

import sqlalchemy as sa
from alembic import context, op

from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

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
    _check_visit_null_filter()
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
    assert bind is not None
    schema = mig_context.version_table_schema

    inspector = sa.inspect(bind)
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
                    batch_op.alter_column(other_element, nullable=nullable)  # type: ignore[attr-defined]

    attributes.update_manager_version(MANAGER, manager_version)


def _check_visit_null_filter() -> None:
    """In some cases we saw that visit.physical_filter column contains NULLs,
    and we need to replace that with some non-NULL values.
    """
    mig_context = context.get_context()
    bind = mig_context.bind
    assert bind is not None
    schema = mig_context.version_table_schema
    metadata = sa.schema.MetaData(schema=schema)

    visit = sa.schema.Table("visit", metadata, autoload_with=bind, schema=schema)
    sql = (
        sa.select(sa.func.count())
        .select_from(visit)
        .where(visit.columns["physical_filter"] == None)  # noqa: E711
    )
    num_nulls = cast(int, bind.execute(sql).scalar())
    if num_nulls > 0:
        # User needs to pass special argument.
        config = context.config
        null_filter_value = config.get_section_option("daf_butler_migrate_options", "null_filter_value")
        if null_filter_value is None:
            raise ValueError(
                "NULL values were found for visit.physical_filter. They need to be replaced with"
                " non-NULL values. Please use `--options null_filter_value=<value>` command line option."
            )
        else:
            op.execute(
                visit.update()
                .where(visit.columns["physical_filter"] == None)  # noqa: E711
                .values(physical_filter=null_filter_value)
            )
