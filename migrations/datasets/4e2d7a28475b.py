"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 2.0.0.

Revision ID: 4e2d7a28475b
Revises: 2101fbf51ad3
Create Date: 2023-03-31 22:25:32.651155

"""

import datetime
import itertools
import logging
from collections.abc import Callable
from typing import Any

import sqlalchemy as sa
from alembic import context, op
from astropy.time import Time
from lsst.daf.butler.core.time_utils import TimeConverter
from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

# revision identifiers, used by Alembic.
revision = "4e2d7a28475b"
down_revision = "2101fbf51ad3"
branch_labels = None
depends_on = None

_LOG = logging.getLogger(f"lsst.daf.butler_migrate.{__name__}")

# Manager name
MANAGER = (
    "lsst.daf.butler.registry.datasets.byDimensions._manager.ByDimensionsDatasetRecordStorageManagerUUID"
)

_EPOCH = datetime.datetime(1970, 1, 1)


def _convert_to_ns(dt: datetime.datetime) -> int:
    """Convert datetime to TAI nanoseconds."""
    return TimeConverter().astropy_to_nsec(Time(dt, scale="utc").tai)


def _convert_to_datetime(nsec: int) -> datetime.datetime:
    """Convert TAI nanoseconds to datetime."""
    timestamp = TimeConverter().nsec_to_astropy(nsec)
    return timestamp.utc.to_datetime()


def upgrade() -> None:
    """Upgrade from version 1.0.0 to version 2.0.0.

    Summary of changes:

        - ingest_date column type changed from database-native TIMESTAMP
          to nanoseconds-since-epoch in TAI scale.
    """
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        print(
            "*** Note that this migration script converts ingest_date TIMESTAMP, which is\n"
            "*** in UTC, to nanoseconds in TAI scale. It uses constant offset of 37 seconds\n"
            "*** between UTC and TAI. This should produce exact values for reasonably\n"
            "*** recent ingest_date values, but may not be exact for other cases.\n"
        )
        # Tell postgres to convert timestamp to nanoseconds, but keep it at
        # microsecond resolution, and add 37 seconds for TAI-UTC difference.
        using = "CAST((EXTRACT(EPOCH FROM ingest_date) + 37) * 1000000 AS BIGINT) * 1000"
        _migrate_pg(sa.BIGINT, None, using, "2.0.0")
    else:
        _migrate_default(sa.BIGINT, None, _convert_to_ns, "2.0.0")


def downgrade() -> None:
    """Downgrade from version 2.0.0 to version 1.0.0."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        print(
            "*** Note that this migration script converts ingest_date from nanoseconds in\n"
            "*** TAI scale to UTC TIMESTAMP. It uses constant offset of 37 seconds between\n"
            "*** UTC and TAI. This should produce exact values for reasonably recent\n"
            "*** ingest_date values, but may not be exact for other cases.\n"
        )
        # Convert from nanoseconds to timestamp and subtract 37 seconds of
        # TAI-UTC difference. TO_TIMESTAMP returns timestamp with timezone, and
        # `_migrate_pg` does SET TIME ZONE 0 to keep things consistent.
        using = "TO_TIMESTAMP(ingest_date / 1000000000. - 37)"
        _migrate_pg(sa.TIMESTAMP, sa.sql.func.now(), using, "1.0.0")
    else:
        _migrate_default(sa.TIMESTAMP, sa.sql.func.now(), _convert_to_datetime, "1.0.0")


def _migrate_default(
    column_type: type,
    server_default: Any,
    convert_method: Callable[[datetime.datetime], int] | Callable[[int], datetime.datetime],
    version: str,
) -> None:
    """Default migration method that does not rely on optimizations.

    This method creates a temporary table which is filled with the converted
    timestamps, and then updates dataset table from that temporary table. This
    was only tested with SQLite, may not work with other backends.
    """
    mig_context = context.get_context()
    bind = op.get_bind()
    assert bind is not None, "Migration only works on actual connection."
    schema = mig_context.version_table_schema
    metadata = sa.schema.MetaData(schema=schema)

    table = sa.schema.Table("dataset", metadata, autoload_with=bind, schema=schema)

    # Create a temporary table.
    tmp_table = sa.schema.Table(
        "dataset_migration_tmp",
        metadata,
        sa.schema.Column("id", table.columns["id"].type, primary_key=True),
        sa.schema.Column("ingest_date", column_type, nullable=False),
        prefixes=["TEMPORARY"],
        schema=sa.schema.BLANK_SCHEMA,
    )
    tmp_table.create(bind)

    # There may be very many records in dataset table to fit everything in
    # memory, so split the whole thing on dataset_type_id.
    query = sa.select(table.columns["dataset_type_id"]).select_from(table).distinct()
    result = bind.execute(query).scalars()
    dataset_type_ids = sorted(result)
    _LOG.info("Found %s dataset types in dataset table", len(dataset_type_ids))

    for dataset_type_id in dataset_type_ids:
        # Extract ingest date for datasets.
        query = (
            sa.select(table.columns["id"], table.columns["ingest_date"])
            .select_from(table)
            .where(table.columns["dataset_type_id"] == dataset_type_id)
        )
        result = bind.execute(query)
        rows = [(dataset_id, convert_method(ingest_date)) for dataset_id, ingest_date in result]
        _LOG.info("Found %s rows for in dataset type %s", len(rows), dataset_type_id)

        iterator = iter(rows)
        count = 0
        while chunk := list(itertools.islice(iterator, 1000)):
            query = tmp_table.insert().values(chunk)
            result = bind.execute(query)
            count += result.rowcount
        _LOG.info("Inserted %s rows into temporary table", count)

    with op.batch_alter_table("dataset", schema) as batch_op:
        if server_default is None:
            # If removing a default it has to be done first
            batch_op.alter_column("ingest_date", server_default=None)  # type: ignore[attr-defined]
    with op.batch_alter_table("dataset", schema) as batch_op:
        # Change the type of the column.
        batch_op.alter_column(  # type: ignore[attr-defined]
            "ingest_date", type_=column_type, server_default=server_default
        )

    # Update ingest date from a temporary table.
    query = table.update().values(
        ingest_date=sa.select(tmp_table.columns["ingest_date"])
        .where(tmp_table.columns["id"] == table.columns["id"])
        .scalar_subquery()
    )
    result = bind.execute(query)
    _LOG.info("Updated %s rows in dataset table", result.rowcount)

    # Update manager schema version.
    attributes = ButlerAttributes(bind, schema)
    attributes.update_manager_version(MANAGER, version)


def _migrate_pg(
    column_type: type,
    server_default: Any,
    using: str,
    version: str,
) -> None:
    """Migration method with PostgreSQL-specific optimizations.

    Notes
    -----
    Postgres allows in-place type update with re-calculation of the new data
    values with its special USING syntax which provides an expression for
    calculating new data values.
    """
    mig_context = context.get_context()
    bind = op.get_bind()
    assert bind is not None, "Migration only works on actual connection."
    schema = mig_context.version_table_schema

    # Some conversions may involve conversion of timestamps, make sure
    # everything is done in UTC.
    bind.execute(sa.text("SET TIME ZONE 0"))

    _LOG.info("Start updating dataset table")
    # Change the type of the column.
    if server_default is None:
        # If removing a default it has to be done first
        op.alter_column("dataset", "ingest_date", schema=schema, server_default=None)
    op.alter_column(
        "dataset",
        "ingest_date",
        schema=schema,
        type_=column_type,
        server_default=server_default,
        postgresql_using=using,
    )
    _LOG.info("Finished updating dataset table")

    # Update manager schema version.
    attributes = ButlerAttributes(bind, schema)
    attributes.update_manager_version(MANAGER, version)
