"""Migration script for SynthIntKeyCollectionManager 2.0.0.

Revision ID: 8c57494cabcc
Revises: 93341d68b814
Create Date: 2023-12-08 11:25:33.984476

"""
import contextlib
import logging
import pprint
from collections.abc import Iterator
from typing import NamedTuple

import sqlalchemy
from alembic import context, op

from lsst.daf.butler_migrate import naming
from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

# revision identifiers, used by Alembic.
revision = "8c57494cabcc"
down_revision = "93341d68b814"
branch_labels = None
depends_on = None

_LOG = logging.getLogger(f"lsst.{__name__}")

# Names of static tables to migrate.
STATIC_TABLES = (
    "dataset",
    "collection",
    "collection_chain",
    "run",
)

# Prefixes of the dynamic tables to migrate.
DYNAMIC_TABLES_PREFIX = (
    "collection_summary_",
    "dataset_calibs_",
    "dataset_tags_",
)

# Per-table column mapping, map existing column name to the new column name.
# Empty table name is used as default, applies to all dynamic tables.
COLUMN_MAP = {
    "collection": {"name": "collection_id"},
    "collection_chain": {"parent": "parent", "child": "child"},
    "run": {"name": "collection_id"},
    "dataset": {"run_name": "run_id"},
    "": {"collection_name": "collection_id"},
}


@contextlib.contextmanager
def _reflection_bind() -> Iterator[sqlalchemy.engine.Connection]:
    """Return database connection to be used for reflection. In online mode
    this returns connection instantiated by Alembic, in offline mode it creates
    new angine using configured URL.

    Yields
    ------
    connection : `sqlalchemy.engine.Connection`
        Actual connection to database to use for reflection.
    """
    if context.is_offline_mode():
        url = context.config.get_main_option("sqlalchemy.url")
        if url is None:
            raise ValueError("sqlalchemy.url is missing from config")
        engine = sqlalchemy.create_engine(url)
        with engine.connect() as connection:
            yield connection
    else:
        yield op.get_bind()


class TableInfo(NamedTuple):
    """Info about table reflected from database before migration."""

    primary_key: sqlalchemy.engine.interfaces.ReflectedPrimaryKeyConstraint
    foreign_keys: list[sqlalchemy.engine.interfaces.ReflectedForeignKeyConstraint]
    unique_constraints: list[sqlalchemy.engine.interfaces.ReflectedUniqueConstraint]
    indices: list[sqlalchemy.engine.interfaces.ReflectedIndex]


def upgrade() -> None:
    """Migrate collection PK from string to integer.

    Summary of changes to the schema:

        - Create `collection_seq_collection_id` sequence.
        - Add `collection.collection_id` column, populate it from the sequence.
        - Add `collection_id` column to all other table, populate it from
          `collection.collection_id`.
        - Drop name columns from all tables, excluding `collection`.
        - Re-add PK to each table (old PKs dropped when columns were removed).
        - Re-add foreign keys and all indices that use names.
    """
    mig_context = context.get_context()
    bind = op.get_bind()
    dialect = bind.dialect
    if dialect.name != "postgresql":
        raise TypeError(f"This migration does not support {dialect.name} dialect")

    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes
    schema = mig_context.version_table_schema
    _LOG.debug("dialect: %r schema: %r, bind: %r", dialect, schema, bind)

    # reflect schema from database
    metadata = sqlalchemy.schema.MetaData(schema=schema)
    with _reflection_bind() as conn:
        metadata.reflect(conn)

    all_tables = _all_tables(schema)
    dynamic_tables = [table for table in all_tables if table not in STATIC_TABLES]

    # Lock all tables to avoid issues.
    _lock_tables(all_tables, schema)

    table_infos = _reflect_tables(schema, all_tables)

    # Add new columns with collection_id to all relevant tables.
    _extend_collection_table(metadata)

    _add_id_column(
        metadata, "run", "name", "collection_id", "collection", "name", "collection_id", schema=schema
    )
    _add_id_column(metadata, "dataset", "run_name", "run_id", "run", "name", "collection_id", schema=schema)

    _add_id_column(
        metadata,
        "collection_chain",
        "parent",
        "parent_id",
        "collection",
        "name",
        "collection_id",
        schema=schema,
    )
    _add_id_column(
        metadata,
        "collection_chain",
        "child",
        "child_id",
        "collection",
        "name",
        "collection_id",
        schema=schema,
    )

    for table_name in dynamic_tables:
        _add_id_column(
            metadata,
            table_name,
            "collection_name",
            "collection_id",
            "collection",
            "name",
            "collection_id",
            schema=schema,
        )

    # Drop old columns, need to do it in reverse order.
    for table_name in reversed(dynamic_tables):
        op.drop_column(table_name, "collection_name", schema=schema)

    op.drop_column("collection_chain", "parent", schema=schema)
    op.alter_column("collection_chain", "parent_id", new_column_name="parent", schema=schema)
    op.drop_column("collection_chain", "child", schema=schema)
    op.alter_column("collection_chain", "child_id", new_column_name="child", schema=schema)

    op.drop_column("dataset", "run_name", schema=schema)
    op.drop_column("run", "name", schema=schema)

    # Update metadata to see new columns.
    if not context.is_offline_mode():
        metadata = sqlalchemy.schema.MetaData(schema=schema)
        metadata.reflect(bind)

    # Change PKs, need to drop old PK from collection table first.
    _make_pk("collection", table_infos["collection"], schema=schema, drop_existing=True)
    _make_pk("run", table_infos["run"], schema=schema)
    _make_pk("collection_chain", table_infos["collection_chain"], schema=schema)
    for table_name in dynamic_tables:
        _make_pk(table_name, table_infos[table_name], schema=schema)

    # Add all other constraints and indices.
    for table_name in all_tables:
        _make_fks(table_name, table_infos, schema=schema)
        _make_unique(table_name, table_infos[table_name], schema=schema)
        _make_indices(table_name, table_infos[table_name], schema=schema)

    # update version in butler_attributes table
    _update_butler_attributes(bind, schema)


def _all_tables(schema: str | None) -> list[str]:
    """Return list of table names that should be migrated.

    Returned tables are ordered based on their FK (in CREATE order).
    """
    with _reflection_bind() as conn:
        inspector = sqlalchemy.inspect(conn)
        tables = [
            table
            for table, _ in inspector.get_sorted_table_and_fkc_names(schema)
            if table and (table in STATIC_TABLES or table.startswith(DYNAMIC_TABLES_PREFIX))
        ]
    _LOG.debug("_all_tables: %s", tables)
    return tables


def _lock_tables(tables: list[str], schema: str | None) -> None:
    """Lock all tables that need to be migrated to avoid conflicts."""

    connection = op.get_bind()
    for table in tables:
        # We do not need quoting for schema/table names.
        if schema:
            query = f"LOCK TABLE {schema}.{table} IN EXCLUSIVE MODE"
        else:
            query = f"LOCK TABLE {table} IN EXCLUSIVE MODE"
        _LOG.info("Locking table %s", table)
        connection.execute(sqlalchemy.text(query))


def _reflect_tables(schema: str | None, table_names: list[str]) -> dict[str, TableInfo]:
    """Extract constraints and indices info for specified tables.

    Parameters
    ----------
    schema : `str`
        Schema name.
    table_names : `list` [`str`]
        List of table names to reflect.

    Returns
    -------
    infos : `dict` [`str`, `TableInfo`]
        Reflected information for the tables.
    """
    table_infos: dict[str, TableInfo] = {}
    with _reflection_bind() as conn:
        inspector = sqlalchemy.inspect(conn)

        for table in table_names:
            pk = inspector.get_pk_constraint(table, schema)
            fks = inspector.get_foreign_keys(table, schema)
            uniques = inspector.get_unique_constraints(table, schema)
            indices = inspector.get_indexes(table, schema)

            table_infos[table] = TableInfo(
                primary_key=pk, foreign_keys=fks, unique_constraints=uniques, indices=indices
            )
            _LOG.debug("TableInfo for %r: %s", table, table_infos[table])

    return table_infos


def _remap_columns(table: str, columns: list[str]) -> list[str] | None:
    """Map pre-migration column names to new column names.

    Parameters
    ----------
    table : `str`
        Table name.
    columns : `list` [`str`]
        List of columns names.

    Returns
    -------
    new_columns : `list` [`str`] or `None`
        `None` is returned if ``columns`` does not include any migrated column.
        Otherwise returns the list where migrated columns are replaced with the
        new names and non-migrated are retained.
    """
    if table in COLUMN_MAP:
        column_map = COLUMN_MAP[table]
    else:
        column_map = COLUMN_MAP[""]
    if set(columns).isdisjoint(column_map):
        # Means that none of the columns changed, skip.
        return None
    return [column_map.get(column, column) for column in columns]


def _make_pk(
    table: str,
    table_info: TableInfo,
    *,
    schema: str | None = None,
    drop_existing: bool = False,
) -> None:
    """Re-create primary key for a table.

    Parameters
    ----------
    table : `str`
        Table name.
    table_info : `TableInfo`
        Corresponding table information.
    schema : `str`, optional
        Database schema name.
    drop_existing : `bool`
        If `True` then drop existing PK first (only needed for ``collections``
        table).
    """
    # Look at the old PK definition and substitute new column names.
    old_columns = table_info.primary_key["constrained_columns"]
    columns = _remap_columns(table, old_columns)
    if columns is None:
        return

    _report_table_size("before adding PK", table, schema)
    pk_name = naming.primary_key_name(table, op.get_bind())
    if drop_existing:
        _LOG.info("Dropping PK on table %s", table)
        op.drop_constraint(pk_name, "collection", schema=schema)
    _LOG.info("Add PK %s to table %s (%s)", pk_name, table, columns)
    op.create_primary_key(pk_name, table, columns, schema=schema)
    _report_table_size("after adding PK", table, schema)


def _make_fks(table: str, table_infos: dict[str, TableInfo], *, schema: str | None = None) -> None:
    """Re-create foreign keys for a table.

    Parameters
    ----------
    table : `str`
        Table name.
    table_infos : `dict` [`str`, `TableInfo`]
        Table information for all tables.
    schema : `str`, optional
        Database schema name.
    """
    _report_table_size("before adding FKs", table, schema)
    for fk in table_infos[table].foreign_keys:
        new_columns = _remap_columns(table, fk["constrained_columns"])
        if new_columns is None:
            continue
        ref_table = fk["referred_table"]
        ref_columns = _remap_columns(ref_table, fk["referred_columns"])
        assert ref_columns is not None, "If referencing columns changed then referred must change too"

        fk_name = naming.foreign_key_name(table, new_columns, ref_table, ref_columns, op.get_bind())
        _LOG.info("Add FK %s to table %s %s -> %s %s", fk_name, table, new_columns, ref_table, ref_columns)
        # Reuse options from old FK.
        options = fk.get("options", {})
        op.create_foreign_key(
            fk_name,
            table,
            ref_table,
            new_columns,
            ref_columns,
            source_schema=schema,
            referent_schema=schema,
            **options,
        )
    _report_table_size("after adding FKs", table, schema)


def _make_unique(table: str, table_info: TableInfo, *, schema: str | None = None) -> None:
    """Re-create unique constraints for a table.

    Parameters
    ----------
    table : `str`
        Table name.
    table_info : `TableInfo`
        Corresponding table information.
    schema : `str`, optional
        Database schema name.
    """
    for uniq in table_info.unique_constraints:
        new_columns = _remap_columns(table, uniq["column_names"])
        if new_columns is None:
            continue

        _report_table_size("before adding unique key", table, schema)
        unique_name = naming.unique_key_name(table, new_columns, op.get_bind())
        _LOG.info("Add unique constraint %s to table %s %s", unique_name, table, new_columns)
        op.create_unique_constraint(unique_name, table, new_columns, schema=schema)
        _report_table_size("after adding unique key", table, schema)


def _make_indices(table: str, table_info: TableInfo, *, schema: str | None = None) -> None:
    """Re-create unique constraints for a table.

    Parameters
    ----------
    table : `str`
        Table name.
    table_info : `TableInfo`
        Corresponding table information.
    schema : `str`, optional
        Database schema name.

    Notes
    -----
    Existing indices include "regular" indices, FK indices and unique indices.
    We create unique indices in _make_unique, here we only make regular and FK
    indices. The only way to guess which is which is to look at the existing
    index name.
    """
    _report_table_size("before adding indices", table, schema)
    for index in table_info.indices:
        if index["name"] is None:
            continue
        if naming.is_foreign_key_index(table, index["name"]):
            fk_index = True
        elif naming.is_regular_index(table, index["name"]):
            fk_index = False
        else:
            continue

        # Check for expression indices, we do not support them.
        columns = [column for column in index["column_names"] if column is not None]
        if len(columns) != len(index["column_names"]):
            continue
        new_columns = _remap_columns(table, columns)
        if new_columns is None:
            continue

        if fk_index:
            idx_name = naming.foreign_key_index_name(table, new_columns, op.get_bind())
            _LOG.info("Add FK index %s to table %s %s", idx_name, table, new_columns)
        else:
            idx_name = naming.index_name(table, new_columns, op.get_bind())
            _LOG.info("Add index %s to table %s %s", idx_name, table, new_columns)
        op.create_index(idx_name, table, new_columns, schema=schema)
    _report_table_size("after adding indices", table, schema)


def _extend_collection_table(metadata: sqlalchemy.schema.MetaData) -> None:
    """Add collection_id column to collection table and fill it with IDs."""
    mig_context = context.get_context()
    bind = op.get_bind()
    schema = mig_context.version_table_schema

    table_name = "collection"
    column_name = "collection_id"

    # Have to make a sequence explicitly, alembic does not support Sequence in
    # column definition.
    seq_name = naming.sequence_name(table_name, column_name, bind)
    sequence = sqlalchemy.Sequence(seq_name, metadata=metadata)
    _LOG.info("Creating sequence for collection ID: %s", seq_name)
    sequence.create(bind)

    _report_table_size("before adding collection_id", table_name, schema)
    # Add collection_id column to collection table, it has to be nullable
    # initially, will be changed after we fill it.
    new_column = sqlalchemy.schema.Column(column_name, sqlalchemy.BigInteger, nullable=True)
    _LOG.info("Adding column %s to table %s", column_name, table_name)
    op.add_column(table_name, new_column, schema=schema)
    _report_table_size("after adding collection_id", table_name, schema)

    # Fill collection_id.
    _LOG.info("Filling column %s.%s with IDs", table_name, column_name)
    table = _get_table(metadata, table_name)
    table.append_column(sqlalchemy.schema.Column(column_name, sqlalchemy.BigInteger, nullable=True))
    update = table.update().values(collection_id=sequence.next_value())
    op.execute(update)
    _report_table_size("after filling collection_id", table_name, schema)

    # Make it NOT NULL
    _LOG.info("Set NOT NULL on column %s.%s", table_name, column_name)
    op.alter_column(table_name, column_name, nullable=False, schema=schema)


def _add_id_column(
    metadata: sqlalchemy.schema.MetaData,
    table_name: str,
    name_column: str,
    id_column: str,
    parent_table: str,
    parent_name_column: str,
    parent_id_column: str,
    *,
    schema: str | None = None,
) -> None:
    """Add new column for collection_id and populate it from parent table.

    Parameters
    ----------
    metadata : `sqlalchemy.schema.MetaData`
        Metadata for database tables.
    table_name : `str`
        Table name to add new column to.
    name_column : `str`
        Existing column in this table holding collection name.
    id_column : `str`
        Name of the new column to add.
    parent_table : `str`
        Name of the parent table that ``table_name`` refers to and which
        already has dataset_id column populated.
    parent_name_column : `str`
        Name of the column in parent table holding collection names.
    parent_id_column : `str`
        Name of the column in parent table holding collection IDs.
    """
    _LOG.info("Add column %s to table %s", id_column, table_name)
    _report_table_size("before adding column", table_name, schema)

    new_column = sqlalchemy.schema.Column(id_column, sqlalchemy.BigInteger, nullable=True)
    op.add_column(table_name, new_column, schema=schema)
    _report_table_size("after adding column", table_name, schema)

    # Fill collection_id.
    table = _get_table(metadata, table_name)
    parent = _get_table(metadata, parent_table)

    table.append_column(sqlalchemy.schema.Column(id_column, sqlalchemy.BigInteger, nullable=True))

    # Correlated subquery to select collection id from parent table.
    subq = sqlalchemy.sql.select(parent.columns[parent_id_column]).where(
        parent.columns[parent_name_column] == table.columns[name_column]
    )
    update = table.update().values({id_column: subq.scalar_subquery()})
    _LOG.info("Fill column %s.%s from %s.%s", table_name, id_column, parent_table, parent_id_column)
    op.execute(update)
    _report_table_size("after filling column", table_name, schema)

    # Make it NOT NULL
    _LOG.info("Set NOT NULL on column %s.%s", table_name, id_column)
    op.alter_column(table_name, id_column, nullable=False, schema=schema)


def _get_table(metadata: sqlalchemy.schema.MetaData, name: str) -> sqlalchemy.schema.Table:
    """Return sqlalchemy Table instance.

    If schema names are used then schema is a part of the key but I do not
    want to depend on that, so just iterate and find matching name.
    """
    tables = [table for table in metadata.tables.values() if table.name == name]
    if not tables:
        raise LookupError("Failed to find table %r in schema", name)
    return tables.pop()


def _report_table_size(message: str, table: str, schema: str | None = None) -> None:
    """Print information about table sizes."""
    if context.is_offline_mode():
        # It's not worth the trouble to do it in offline mode.
        return
    if schema:
        query = (
            "select pg_table_size(quote_ident(:schema) || '.' || quote_ident(:table)), "
            "pg_indexes_size(quote_ident(:schema) || '.' || quote_ident(:table)), "
            "pg_total_relation_size(quote_ident(:schema) || '.' || quote_ident(:table))"
        )
    else:
        query = (
            "select pg_table_size(quote_ident(:table)), "
            "pg_indexes_size(quote_ident(:table)), "
            "pg_total_relation_size(quote_ident(:table))"
        )

    connection = op.get_bind()
    result = connection.execute(sqlalchemy.text(query), {"schema": schema, "table": table})
    table_size, indices_size, total = result.one()
    # Print numbers with thousand separators.
    pp = pprint.PrettyPrinter(underscore_numbers=True)
    _LOG.info(
        "%s table size %s: table=%s, indices=%s, total=%s",
        table,
        message,
        pp.pformat(table_size),
        pp.pformat(indices_size),
        pp.pformat(total),
    )


def _update_butler_attributes(bind: sqlalchemy.engine.Connection, schema: str | None) -> None:
    """Update contents of butler_attributes with new version and digests."""
    _LOG.info("Updating butler_attributes metadata")

    mgr_module = "lsst.daf.butler.registry.collections"
    old_class = "nameKey.NameKeyCollectionManager"
    new_class = "synthIntKey.SynthIntKeyCollectionManager"

    attributes = ButlerAttributes(bind, schema)

    # Remove existing records for old manager.
    attributes.delete(f"version:{mgr_module}.{old_class}")

    # Update manager class name.
    attributes.update("config:registry.managers.collections", f"{mgr_module}.{new_class}")

    # Insert version for new manager.
    attributes.insert(f"version:{mgr_module}.{new_class}", "2.0.0")


def downgrade() -> None:
    """Downgrade is not implemented, it may be relatively easy to do but it is
    likely we'll never need it.
    """
    # raise NotImplementedError()
