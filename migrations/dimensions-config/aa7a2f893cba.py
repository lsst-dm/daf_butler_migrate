"""Migration script for dimensions.yaml namespace=daf_butler version=8.

Revision ID: aa7a2f893cba
Revises: 352c30854bb0
Create Date: 2026-05-05 15:24:24.546869
"""

import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext
from lsst.daf.butler_migrate.naming import primary_key_name, foreign_key_name, foreign_key_index_name

# revision identifiers, used by Alembic.
revision = "aa7a2f893cba"
down_revision = "352c30854bb0"
branch_labels = None
depends_on = None

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")


def upgrade() -> None:
    """Upgrade 'dimensions-config' tree from version 7 to version 8 (ticket
    DM-54838).

    Summary of changes:
      - Add tables for three new solar-system dimensions: ssp_hypothesis_table,
        ssp_hypothesis_bundle, ssp_balanced_index.
    """
    ctx = MigrationContext()

    _LOG.info("Checking that this is an unmodified daf_butler universe 7 repo")
    ctx.attributes.validate_dimensions_json(7)

    table = "ssp_hypothesis_table"
    _LOG.info("Creating table %s", table)
    op.create_table(
        table,
        sa.Column("name", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("name", name=primary_key_name(table, ctx.bind)),
        schema=ctx.schema,
    )

    table = "ssp_hypothesis_bundle"
    parent_table = "ssp_hypothesis_table"
    parent_column = f"{parent_table}.name"
    if ctx.schema:
        parent_column = f"{ctx.schema}.{parent_column}"
    _LOG.info("Creating table %s", table)
    fk_name = foreign_key_name(table, ["ssp_hypothesis_table"], parent_table, ["name"], ctx.bind)
    idx_name = foreign_key_index_name(table, ["ssp_hypothesis_table"], ctx.bind)
    op.create_table(
        table,
        sa.Column("ssp_hypothesis_table", sa.Text, nullable=False),
        sa.Column("id", sa.BigInteger, nullable=False),
        sa.PrimaryKeyConstraint("ssp_hypothesis_table", "id", name=primary_key_name(table, ctx.bind)),
        sa.ForeignKeyConstraint(["ssp_hypothesis_table"], [parent_column], name=fk_name),
        sa.Index(idx_name, "ssp_hypothesis_table"),
        schema=ctx.schema,
    )

    table = "ssp_balanced_index"
    _LOG.info("Creating table %s", table)
    fk_name = foreign_key_name(table, ["ssp_hypothesis_table"], parent_table, ["name"], ctx.bind)
    idx_name = foreign_key_index_name(table, ["ssp_hypothesis_table"], ctx.bind)
    op.create_table(
        table,
        sa.Column("ssp_hypothesis_table", sa.Text, nullable=False),
        sa.Column("id", sa.BigInteger, nullable=False),
        sa.PrimaryKeyConstraint("ssp_hypothesis_table", "id", name=primary_key_name(table, ctx.bind)),
        sa.ForeignKeyConstraint(["ssp_hypothesis_table"], [parent_column], name=fk_name),
        sa.Index(idx_name, "ssp_hypothesis_table"),
        schema=ctx.schema,
    )

    _LOG.info("Updating dimensions.json in ButlerAttributes")
    ctx.attributes.replace_dimensions_json(8)


def downgrade() -> None:
    """Undo changes applied in `upgrade`."""
    ctx = MigrationContext()

    _LOG.info("Checking that this is an unmodified daf_butler universe 8 repo")
    ctx.attributes.validate_dimensions_json(8)

    _LOG.info("Dropping table ssp_balanced_index")
    op.drop_table("ssp_balanced_index", schema=ctx.schema)

    _LOG.info("Dropping table ssp_hypothesis_bundle")
    op.drop_table("ssp_hypothesis_bundle", schema=ctx.schema)

    _LOG.info("Dropping table ssp_hypothesis_table")
    op.drop_table("ssp_hypothesis_table", schema=ctx.schema)

    _LOG.info("Updating dimensions.json in ButlerAttributes")
    ctx.attributes.replace_dimensions_json(7)
