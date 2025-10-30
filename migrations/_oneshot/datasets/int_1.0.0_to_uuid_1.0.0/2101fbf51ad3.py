"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 635083325f20
Create Date: 2021-05-04 16:31:05.926989

"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, NamedTuple
from collections.abc import Iterator

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects.postgresql import UUID

from lsst.daf.butler_migrate.digests import get_digest

# revision identifiers, used by Alembic.
revision = "2101fbf51ad3"
down_revision = "635083325f20"
branch_labels = None
depends_on = None


_LOG = logging.getLogger(__name__)

NS_UUID = uuid.UUID("840b31d9-05cd-5161-b2c8-00d32b280d0f")
"""Namespace UUID used for UUID5 generation. Do not change. This was
produced by `uuid.uuid5(uuid.NAMESPACE_DNS, "lsst.org")`.
"""

UUID5_DATASET_TYPES = ("raw",)
"""Collection of dataset type names for which we make UUID5 dataset IDs.
"""

ID_MAP_TABLE_NAME = "migration_id2uuid"
"""Name of the temporary ID mapping table"""

STATIC_TABLES = (
    "dataset",
    "dataset_location",
    "dataset_location_trash",
    "file_datastore_records",
)

DYNAMIC_TABLES_PREFIX = (
    "dataset_calibs_",
    "dataset_tags_",
)


class TableInfo(NamedTuple):
    """Info about table reflected from database.

    Information only includes columns that are migrated.
    """

    primary_key: dict | None
    foreign_keys: list[dict]
    unique_constraints: list[dict]
    indices: list[dict]


def upgrade() -> None:
    """Change type of the primary key colum in dataset table from int to UUID.

    This is a rather complicated migration, and here is the list of changes
    that we need to do:

    - PK column on dataset table changes from int to uuid (native uuid type
      in Postgres, CHAR(32) in sqlite).
    - The value of the column needs to be generated in Python, it is either
      random UUID4, or UUID5 depending on dataset type.
    - All tables that reference dataset table need their FK column type changed
      and values updated to match new UUID values.

    The plan for implementing that:

    - Create temporary table for mapping integer IDs into UUIDs, fill it based
      run name, dataset type, and dataId for each dataset ID.
    - Add new column to dataset table with a temporary name (e.g. `id_uuid`),
      with type matching UUID type, non-indexed, with default NULL.
    - Add `dataset_id_uuid` column to each dependent table.
    - Fill values in the UUID column using join with a mapping table.
    - Drop all constraints and indices that use `dataset_id` column in
      dependent tables, and drop `dataset_id` column itself.
    - Remove PK from `dataset` table, drop `id` column, also drop
      `dataset_seq_id` sequence for postgres case.
    - Rename `uuid_id` column to `id`, add PK constraint with the same name as
      before to `dataset` table.
    - For each dependent table rename UUID column to `dataset_id`, re-create
      all constraints and indices.
    """

    # get migration context
    mig_context = context.get_context()
    bind = mig_context.bind
    assert bind is not None
    dialect = bind.dialect
    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes
    schema = mig_context.version_table_schema
    _LOG.debug("dialect: %r schema: %r, bind: %r", dialect, schema, bind)

    # need to know data type for new UUID column, this is dialect-specific
    if dialect.name == "postgresql":
        uuid_type = dialect.type_descriptor(UUID())
    else:
        uuid_type = dialect.type_descriptor(sa.CHAR(32))  # type: ignore[arg-type]
    _LOG.debug("uuid_type: %r", uuid_type)

    # get names of tables that need migration, ordered by dependencies
    table_names = _tables_to_migrate(schema)

    table_info = _get_table_info(schema, table_names)

    # create id -> uuid mapping table
    _make_id_map(schema, uuid_type)

    # add uuid column to each table that needs it
    for table_name in table_names:
        _add_uuid_column(table_name, uuid_type, schema)

    # reflect schema from database
    metadata = sa.schema.MetaData(schema=schema)
    metadata.reflect(bind)

    # generate id -> uuid mapping
    _fill_id_map(bind, metadata)

    # fill uuid column in the tables
    map_table = _get_table(metadata, ID_MAP_TABLE_NAME)
    for table_name in table_names:
        table = _get_table(metadata, table_name)
        _fill_uuid_column(table, map_table)

    # drop existing constraints, indices, and columns; has to be done in
    # reverse order
    for table_name in reversed(table_names):
        _drop_columns(table_name, table_info[table_name], schema)

    # rename uuid columns
    for table_name in table_names:
        _rename_column(table_name, schema)

    # re-create indices and constraints
    for table_name in table_names:
        _make_indices(table_name, table_info[table_name], schema)

    # drop mapping table
    _LOG.debug("Dropping mapping table")
    op.drop_table(ID_MAP_TABLE_NAME, schema=schema)

    # refresh schema from database
    metadata = sa.schema.MetaData(schema=schema)
    metadata.reflect(bind)

    # update version in butler_attributes table
    _update_butler_attributes(metadata)


def downgrade() -> None:
    """Downgrade is not implemented, it may be relatively easy to do but it is
    likely we never need it.
    """
    raise NotImplementedError()


def _tables_to_migrate(schema: str) -> list[str]:
    """Return list of table names that should be migrated.

    Tables are ordered based on their FK relation.
    """
    inspector = sa.inspect(op.get_bind())
    tables = [
        table
        for table, _ in inspector.get_sorted_table_and_fkc_names(schema)
        if table and (table in STATIC_TABLES or table.startswith(DYNAMIC_TABLES_PREFIX))
    ]
    _LOG.debug("_tables_to_migrate: %s", tables)
    return tables


def _get_table_info(schema: str, table_names: list[str]) -> dict[str, TableInfo]:
    """Extract constraints and indices info for all tables.

    This only returns indices and constraints that use dataset id column.
    """
    inspector = sa.inspect(op.get_bind())

    table_info: dict[str, TableInfo] = {}
    for table in table_names:
        id_col = _id_column_name(table)

        constr = inspector.get_pk_constraint(table, schema)
        pk = None if constr and id_col not in constr["constrained_columns"] else constr
        fks = inspector.get_foreign_keys(table, schema)
        fks = [fk for fk in fks if id_col in fk["constrained_columns"]]
        uniques = inspector.get_unique_constraints(table, schema)
        uniques = [unq for unq in uniques if id_col in unq["column_names"]]
        indices = inspector.get_indexes(table, schema)
        indices = [idx for idx in indices if id_col in idx["column_names"]]

        table_info[table] = TableInfo(
            primary_key=pk, foreign_keys=fks, unique_constraints=uniques, indices=indices  # type:ignore
        )
        _LOG.debug("TableInfo for %r: %s", table, table_info[table])

    return table_info


def _get_table(metadata: sa.schema.MetaData, name: str) -> sa.schema.Table:
    """Return sqlalchemy Table instance.

    If schema names are used then schema is a part of the key but I do not
    want to depend on that, so just iterate and find matching name.
    """
    tables = [table for table in metadata.tables.values() if table.name == name]
    if not tables:
        raise LookupError("Failed to find table %r in schema", name)
    return tables.pop()


def _make_id_map(schema: str, uuid_type: Any) -> None:
    """Create id -> uuid mapping table."""
    _LOG.info("creating %s table", ID_MAP_TABLE_NAME)
    op.create_table(
        ID_MAP_TABLE_NAME,
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("uuid", uuid_type),
        schema=schema,
    )


def _fill_id_map(bind: sa.engine.Connection, metadata: sa.schema.MetaData) -> None:
    """Fill mapping table generating UUIDs according to policies."""
    table = _get_table(metadata, ID_MAP_TABLE_NAME)

    dialect = op.get_bind().dialect

    start_time = time.time()
    count = 0
    batch: list[dict[str, Any]] = []
    for run_name, dstype_name, dataset_id, dataId in _gen_refs(bind, metadata):
        dataset_uuid = _makeDatasetId(run_name, dstype_name, dataId)
        # _LOG.debug("dataset_id: %r, run_name: %r, dstype_name: %r , dataId: %r, dataset_uuid: %r",
        #            dataset_id, run_name, dstype_name, dataId, str(dataset_uuid))
        if dialect.name == "sqlite":
            uuid_str = dataset_uuid.hex
        else:
            uuid_str = str(dataset_uuid)
        batch.append({"id": dataset_id, "uuid": uuid_str})

        if len(batch) >= 10000:
            op.bulk_insert(table, batch, multiinsert=True)
            _LOG.debug("inserted %s rows", len(batch))
            count += len(batch)
            batch = []

    if batch:
        op.bulk_insert(table, batch, multiinsert=True)
        _LOG.debug("inserted %s rows", len(batch))
        count += len(batch)
        batch = []

    end_time = time.time()
    _LOG.info(
        "inserted total %s rows into %s in %.3f seconds", count, ID_MAP_TABLE_NAME, end_time - start_time
    )


def _gen_refs(
    bind: sa.engine.Connection, metadata: sa.schema.MetaData
) -> Iterator[tuple[str, str, int, dict[str, Any]]]:
    """Generate "refs" and run names for all datasets.

    Yields
    ------
    run : `str`
        Name of run collection for a dataset.
    dataset_type : `str`
        Name of dataset type.
    dataset_id : `int`
        Dataset id.
    dataId : `dict`
        Possibly empty dictionary representing DataId.
    """
    dataset = _get_table(metadata, "dataset")
    dataset_type = _get_table(metadata, "dataset_type")
    run = _get_table(metadata, "run")
    collection = _get_table(metadata, "collection")

    dataset_ids = set()

    tag_tables = [table for table in metadata.tables.values() if table.name.startswith("dataset_tags_")]
    for table in tag_tables:
        # All columns except few are dimension columns. It is possible to
        # extract names from a dataset type and it related graph but that is a
        # bit more complex.
        dim_cols = [
            col
            for col in table.columns
            if col.name
            not in ("dataset_id", "dataset_id_uuid", "dataset_type_id", "collection_name", "collection_id")
        ]
        _LOG.debug("Making refs from %r table, dim_names: %s", table.name, [col.name for col in dim_cols])

        # Non-dimension columns
        col_dataset_type_name = dataset_type.columns.name
        col_dataset_id = table.columns.dataset_id
        col_collection_name = collection.columns.name

        select_from = dataset_type.join(dataset).join(run).join(collection)

        if "collection_id" in collection.columns:
            select_from = select_from.join(
                table,
                sa.and_(
                    dataset.columns.id == table.columns.dataset_id,
                    table.columns.collection_id == collection.columns.collection_id,
                ),
            )
        else:
            select_from = select_from.join(
                table,
                sa.and_(
                    dataset.columns.id == table.columns.dataset_id,
                    table.columns.collection_name == collection.columns.name,
                ),
            )

        sql = sa.select(col_dataset_type_name, col_dataset_id, col_collection_name, *dim_cols).select_from(
            select_from
        )
        _LOG.debug("sql: %s", sql)
        result = bind.execute(sql)

        for row in result.mappings():
            run_name = row[col_collection_name]
            dstype_name = row[col_dataset_type_name]
            dataset_id = row[col_dataset_id]
            dataId = dict((col.name, row[col]) for col in dim_cols)
            dataset_ids.add(dataset_id)

            yield run_name, dstype_name, dataset_id, dataId

    # Also look at removed datasets that are only known to datastore.
    removed_ids = set()
    for table_name in ("file_datastore_records", "dataset_location_trash"):
        table = _get_table(metadata, table_name)
        col_dataset_id = table.columns["dataset_id"]
        sql = sa.select(col_dataset_id).select_from(table)
        _LOG.debug("sql: %s", sql)
        result = bind.execute(sql)
        for row in result.mappings():
            dataset_id = row[col_dataset_id]
            if dataset_id not in dataset_ids:
                removed_ids.add(dataset_id)
    if removed_ids:
        _LOG.debug("found %s removed datasets", len(removed_ids))
        # Run name and dataset type name can be anything that is non-raw.
        run_name = ""
        dstype_name = ""
        dataId = {}
        for dataset_id in removed_ids:
            yield run_name, dstype_name, dataset_id, dataId


def _makeDatasetId(run_name: str, dstype_name: str, dataId: dict[str, Any]) -> uuid.UUID:
    """Generate dataset ID for a dataset.

    This is a copy of the code from registry, has to produce identical
    output but this also decides which type of UUID to make based on
    dataset type name.

    Returns
    -------
    datasetId : `uuid.UUID`
        Dataset identifier.
    """
    if dstype_name not in UUID5_DATASET_TYPES:
        return uuid.uuid4()
    else:
        # WARNING: If you modify this code make sure that the order of
        # items in the `items` list below never changes.
        items: list[tuple[str, str]] = [
            ("dataset_type", dstype_name),
            ("run", run_name),
        ]

        for name, value in sorted(dataId.items()):
            items.append((name, str(value)))
        data = ",".join(f"{key}={value}" for key, value in items)
        # _LOG.debug("run_name: %r, dstype_name: %r, dataId: %r, data: %r",
        #            run_name, dstype_name, dataId, data)
        return uuid.uuid5(NS_UUID, data)


def _id_column_name(table_name: str) -> str:
    """Return dataset ID column name for a given table."""
    return "id" if table_name == "dataset" else "dataset_id"


def _add_uuid_column(table_name: str, uuid_type: Any, schema: str) -> None:
    """Add new uuid column to the table, column is nullable initially."""
    column_name = _id_column_name(table_name) + "_uuid"
    _LOG.debug("Adding column %r to table %r", column_name, table_name)
    op.add_column(table_name, sa.Column(column_name, uuid_type, nullable=True), schema=schema)

    # Pedantic mode - add column comment
    if table_name == "dataset":
        dialect = op.get_bind().dialect
        if dialect.name == "postgresql":
            comment = "A unique field used as the primary key for dataset."
            op.alter_column(table_name, column_name, comment=comment, schema=schema)


def _fill_uuid_column(table: sa.schema.Table, map_table: sa.schema.Table) -> None:
    """Fill new UUID column in a table using values from existing ID column and
    mapping table.
    """
    # generate UUIDs
    if table.name == "dataset":
        sql = table.update().values(
            id_uuid=sa.select(map_table.columns.uuid)
            .where(map_table.columns.id == table.columns.id)
            .scalar_subquery()
        )
    else:
        sql = table.update().values(
            dataset_id_uuid=sa.select(map_table.columns.uuid)
            .where(map_table.columns.id == table.columns.dataset_id)
            .scalar_subquery()
        )
    op.get_bind().execute(sql)
    _LOG.debug("Filled uuids in table %r", table.name)


def _drop_columns(table_name: str, table_info: TableInfo, schema: str) -> None:
    """Drop existing ID column from a table, removing also aal indices and
    constraints that use it.
    """

    _LOG.debug("Dropping items from %s table schema", table_name)
    id_col = _id_column_name(table_name)

    with op.batch_alter_table(table_name, schema) as batch_op:
        for index_dict in table_info.indices:
            index_name = index_dict["name"]
            _LOG.debug("Dropping index %s", index_dict)
            batch_op.drop_index(index_name)  # type: ignore[attr-defined]

        for unique_dict in table_info.unique_constraints:
            unique_name = unique_dict["name"]
            _LOG.debug("Dropping unique constraint %s", unique_name)
            batch_op.drop_constraint(unique_name)  # type: ignore[attr-defined]

        for fk_dict in table_info.foreign_keys:
            fk_name = fk_dict["name"]
            _LOG.debug("Dropping foreign key %s", fk_name)
            batch_op.drop_constraint(fk_name)  # type: ignore[attr-defined]

        if table_info.primary_key:
            _LOG.debug("Primary key: %s", table_info.primary_key)
            pk_name = table_info.primary_key["name"]
            if pk_name:
                _LOG.debug("Dropping primary key %s", pk_name)
                batch_op.drop_constraint(pk_name)  # type: ignore[attr-defined]
            else:
                dialect = op.get_bind().dialect
                if dialect.name == "sqlite":
                    # In our schema SQLite does not have a name for primary key
                    # for some reason, so there is no way to drop it, but we
                    # have to do it because dropping column may result in a
                    # uniqueness violation. Instead of dropping I try to
                    # redefine the PK.
                    columns = table_info.primary_key["constrained_columns"][:]
                    if len(columns) > 1 and id_col in columns:
                        idx = columns.index(id_col)
                        columns[idx] += "_uuid"
                        _LOG.debug("Creating primary key %s", columns)
                        batch_op.create_primary_key(  # type: ignore[attr-defined]
                            f"{table_name}_pkey", columns
                        )

        # drop column
        _LOG.debug("Dropping column %s", id_col)
        batch_op.drop_column(id_col)  # type: ignore[attr-defined]

    # drop a sequence as well
    if table_name == "dataset":
        dialect = op.get_bind().dialect
        if dialect.name == "postgresql":
            seq = "dataset_seq_id"
            if schema:
                seq = f"{schema}.{seq}"
            _LOG.debug("Dropping sequence %r", seq)
            sql = f"DROP SEQUENCE {seq}"
            op.execute(sql)


def _rename_column(table_name: str, schema: str) -> None:
    """Rename UUID column to its final name, make it NOT NULL."""
    id_col = _id_column_name(table_name)
    _LOG.debug("Renaming uuid column in table %s to %s", table_name, id_col)

    with op.batch_alter_table(table_name, schema) as batch_op:
        batch_op.alter_column(  # type: ignore[attr-defined]
            f"{id_col}_uuid", new_column_name=id_col, nullable=False
        )


def _make_indices(table_name: str, table_info: TableInfo, schema: str) -> None:
    """Re-create all constraint and indices on a table using new UUID column."""

    with op.batch_alter_table(table_name, schema) as batch_op:
        if table_info.primary_key:
            pk_name = table_info.primary_key["name"]
            if pk_name is None:
                pk_name = f"{table_name}_pkey"
            _LOG.debug("Adding primary key %s", pk_name)
            columns = table_info.primary_key["constrained_columns"]
            batch_op.create_primary_key(pk_name, columns)  # type: ignore[attr-defined]

        for unique_dict in table_info.unique_constraints:
            unique_name = unique_dict["name"]
            _LOG.debug("Adding unique constraint %s", unique_name)
            columns = unique_dict["column_names"]
            batch_op.create_unique_constraint(unique_name, columns)  # type: ignore[attr-defined]

        for index_dict in table_info.indices:
            index_name = index_dict["name"]
            _LOG.debug("Adding index %s", index_dict)
            columns = index_dict["column_names"]
            unique = index_dict["unique"]
            batch_op.create_index(index_name, columns, unique=unique)  # type: ignore[attr-defined]

        for fk_dict in table_info.foreign_keys:
            fk_name = fk_dict["name"]
            _LOG.debug("Adding foreign key %s", fk_name)
            ref_table = fk_dict["referred_table"]
            ref_schema = fk_dict["referred_schema"]
            local_cols = fk_dict["constrained_columns"]
            remote_cols = fk_dict["referred_columns"]
            # schema reflection does not provide ONDELETE value, but we know what
            # it should be
            ondelete = None
            if table_name.startswith(DYNAMIC_TABLES_PREFIX):
                ondelete = "CASCADE"
            batch_op.create_foreign_key(  # type: ignore[attr-defined]
                fk_name, ref_table, local_cols, remote_cols, ondelete=ondelete, referent_schema=ref_schema
            )


def _update_butler_attributes(metadata: sa.schema.MetaData) -> None:
    """Update contents of butler_attributes with new version and digests."""
    _LOG.debug("Updating butler_attributes metadata")

    mgr_module = "lsst.daf.butler.registry.datasets.byDimensions._manager"
    old_class = "ByDimensionsDatasetRecordStorageManager"
    new_class = "ByDimensionsDatasetRecordStorageManagerUUID"

    bind = op.get_bind()
    butler_attributes = _get_table(metadata, "butler_attributes")

    sql: sa.sql.expression.Delete | sa.sql.expression.Insert | sa.sql.expression.Update

    # remove existing records for old manager
    sql = butler_attributes.delete().where(
        butler_attributes.columns.name == f"version:{mgr_module}.{old_class}"
    )
    bind.execute(sql)
    sql = butler_attributes.delete().where(
        butler_attributes.columns.name == f"schema_digest:{mgr_module}.{old_class}"
    )
    bind.execute(sql)

    # update manager class name
    sql = (
        butler_attributes.update()
        .values(value=f"{mgr_module}.{new_class}")
        .where(butler_attributes.columns.name == "config:registry.managers.datasets")
    )
    bind.execute(sql)

    # insert version and digest for new manager
    tables = [
        _get_table(metadata, "dataset"),
        _get_table(metadata, "dataset_type"),
    ]
    digest = get_digest(tables, bind.dialect, nullable_columns={"id", "dataset_id"})
    _LOG.debug("new schema digest for datasets manager: %s", digest)
    sql = butler_attributes.insert()
    bind.execute(
        sql,
        [
            {"name": f"version:{mgr_module}.{new_class}", "value": "1.0.0"},
            {"name": f"schema_digest:{mgr_module}.{new_class}", "value": digest},
        ],
    )

    # the change also affects schema digest for one other manager, recalculate
    # digest for MonolithicDatastoreRegistryBridgeManager from new table schema
    manager = "lsst.daf.butler.registry.bridge.monolithic.MonolithicDatastoreRegistryBridgeManager"
    tables = [
        _get_table(metadata, "dataset_location"),
        _get_table(metadata, "dataset_location_trash"),
    ]
    digest = get_digest(tables, bind.dialect, nullable_columns={"dataset_id"})
    _LOG.debug("new schema digest for bridge manager: %s", digest)
    sql = (
        butler_attributes.update()
        .values(value=digest)
        .where(butler_attributes.columns.name == f"schema_digest:{manager}")
    )
    bind.execute(sql)
