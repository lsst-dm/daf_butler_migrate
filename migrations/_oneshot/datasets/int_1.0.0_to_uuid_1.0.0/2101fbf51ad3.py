"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 635083325f20
Create Date: 2021-05-04 16:31:05.926989

"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Tuple
import uuid

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '2101fbf51ad3'
down_revision = '635083325f20'
branch_labels = None
depends_on = None


_LOG = logging.getLogger(__name__)

NS_UUID = uuid.UUID('840b31d9-05cd-5161-b2c8-00d32b280d0f')
"""Namespace UUID used for UUID5 generation. Do not change. This was
produced by `uuid.uuid5(uuid.NAMESPACE_DNS, "lsst.org")`.
"""

UUID5_DATASET_TYPES = ("raw", )
"""Collection of dataset type names for which we make UUID5 dataset IDs.
"""

ID_MAP_TABLE_NAME = "smig_id2uuid"
"""Name of the ID mapping table"""

def upgrade():
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

    - Add new column to dataset table with a temporary name (e.g. `uuid_id`),
      with type matching UUID type, non-indexed, with default NULL.
    - Fill values in that colum based on all other info, this will involve
      reading bunch of other tables.
    - In all dependent tables create new column, fill it with values matching
      content of dataset table.
    - Remove FK constraints from all dependent tables, remember the names of
      constraints, drop `dataset_id` columns.
    - Remove PK from `dataset` table, drop `id` column.
    - Rename `uuid_id` column to `id`, add PK constraint with the same name as
      before.
    - For each dependent table rename new column to `dataset_id`, add FK
      constraint.
    """

    # get migration context
    mig_context = context.get_context()
    bind = mig_context.bind
    dialect = bind.dialect
    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes
    schema = mig_context.version_table_schema
    _LOG.debug("dialect: %r schema: %r, bind: %r", dialect, schema, bind)

    # need to know data type for new UUID column, this is dialect-specific
    if dialect.name == 'postgresql':
        uuid_type = dialect.type_descriptor(UUID())
    else:
        uuid_type = dialect.type_descriptor(sa.CHAR(32))
    _LOG.debug("uuid_type: %r", uuid_type)

    # reflect schema from database
    metadata = sa.schema.MetaData(bind, schema=schema)
    metadata.reflect()
    tables = _tables_to_migrate(metadata)

    # create id -> uuid mapping table
    _make_id_map(metadata, uuid_type)

    # add uuid column to each table that needs it
    for table in tables:
        _add_uuid_column(table.name, uuid_type, schema)

    # refresh schema from database
    metadata = sa.schema.MetaData(bind, schema=schema)
    metadata.reflect()
    tables = _tables_to_migrate(metadata)

    # generate id -> uuid mapping
    _fill_id_map(metadata)

    # fill uuid column in the tables
    map_table = _get_table(metadata, ID_MAP_TABLE_NAME)
    for table in tables:
        _fill_uuid_column(table, map_table)

    # raise NotImplementedError()


def downgrade():
    raise NotImplementedError()


def _tables_to_migrate(metadata: sa.schema.MetaData) -> List[sa.schema.Table]:
    """Return ordered list of tables that should be migrated.

    Tables are ordered based on their FK relation.
    """

    exact_match = (
        "dataset",
        "dataset_location",
        "dataset_location_trash",
        "file_datastore_records",
    )

    start_match = (
        "dataset_calibs_",
        "dataset_tags_",
    )

    tables = [table for table in metadata.sorted_tables
              if table.name in exact_match or table.name.startswith(start_match)]
    _LOG.debug("_tables_to_migrate: %s", [table.name for table in tables])
    return tables


def _get_table(metadata: sa.schema.MetaData, name: str) -> sa.schema.Table:
    # If schema names are used then schema is a part of the key but I do not
    # want to depend on that, so just iterate and find matching name.
    tables = [table for table in metadata.tables.values() if table.name == name]
    if not tables:
        raise LookupError("Failed to find table %r in schema", name)
    return tables.pop()


def _make_id_map(metadata: sa.schema.MetaData, uuid_type: Any):
    """Create id -> uuid mapping table and fill it.
    """
    _LOG.info("creating smig_id2uuid table")
    table = op.create_table(
        ID_MAP_TABLE_NAME,
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("uuid", uuid_type),
        schema=metadata.schema,
    )


def _fill_id_map(metadata: sa.schema.MetaData):

    table = _get_table(metadata, ID_MAP_TABLE_NAME)

    start_time = time.time()
    count = 0
    batch: List[Dict[str, Any]] = []
    for run_name, dstype_name, dataset_id, dataId in _gen_refs(metadata):
        dataset_uuid = _makeDatasetId(run_name, dstype_name, dataId)
        _LOG.debug("dataset_id: %r, run_name: %r, dstype_name: %r , dataId: %r, dataset_uuid: %r",
                   dataset_id, run_name, dstype_name, dataId, str(dataset_uuid))
        batch.append({"id": dataset_id, "uuid": str(dataset_uuid)})

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
    _LOG.info("inserted total %s rows into _smig_ud2uuid in %.3f seconds",
              count, end_time - start_time)


def _gen_refs(metadata: sa.schema.MetaData) -> Iterator[Tuple[str, str, int, Dict[str, Any]]]:
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

    tag_tables = [table for table in metadata.tables.values() if table.name.startswith("dataset_tags_")]
    for table in tag_tables:

        # All columns except few are dimension columns. It is possible to
        # extract names from a dataset type and it related graph but that is a
        # bit more complex.
        dim_cols = [
            col for col in table.columns
            if col.name not in ("dataset_id", "dataset_id_uuid", "dataset_type_id", "collection_name", "collection_id")
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
                sa.and_(dataset.columns.id == table.columns.dataset_id,
                        table.columns.collection_id == collection.columns.collection_id))
        else:
            select_from = select_from.join(
                table,
                sa.and_(dataset.columns.id == table.columns.dataset_id,
                        table.columns.collection_name == collection.columns.name))

        sql = sa.select([
            col_dataset_type_name,
            col_dataset_id,
            col_collection_name,
            *dim_cols,
        ]).select_from(select_from)
        _LOG.debug("sql: %s", sql)
        result = metadata.bind.execute(sql)

        for row in result:
            run_name = row[col_collection_name]
            dstype_name = row[col_dataset_type_name]
            dataset_id = row[col_dataset_id]
            dataId = dict((col.name, row[col]) for col in dim_cols)

            yield run_name, dstype_name, dataset_id, dataId


def _makeDatasetId(run_name: str, dstype_name: str, dataId: Dict[str, Any]) -> uuid.UUID:
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
        items: List[Tuple[str, str]] = [
            ("dataset_type", dstype_name),
            ("run", run_name),
        ]

        for name, value in sorted(dataId.items()):
            items.append((name, str(value)))
        data = ",".join(f"{key}={value}" for key, value in items)
        _LOG.debug("run_name: %r, dstype_name: %r, dataId: %r, data: %r",
                   run_name, dstype_name, dataId, data)
        return uuid.uuid5(NS_UUID, data)


def _add_uuid_column(table_name: str, uuid_type: Any, schema: str) -> None:
    """Add new uuid column to the table.
    """
    if table_name == "dataset":
        column_name = "id_uuid"
    else:
        column_name = "dataset_id_uuid"

    _LOG.debug("Adding column %r to table %r", column_name, table_name)
    op.add_column(
        table_name,
        sa.Column(column_name, uuid_type, nullable=True),
        schema=schema
    )


def _fill_uuid_column(table: sa.schema.Table, map_table: sa.schema.Table) -> None:
    """Create and fill new table replacing ints with UUIDs.

    The newly create table will not have any indices or constraints defined for
    it, this will be done later when original tables are deleted.
    """
    metadata = table.metadata
    table_name = table.name

    # generate UUIDs
    if table.name == "dataset":
        sql = table.update().values(
            id_uuid=map_table.columns.uuid
        ).where(
            map_table.columns.id == table.columns.id
        )
    else:
        sql = table.update().values(
            dataset_id_uuid=map_table.columns.uuid
        ).where(
            map_table.columns.id == table.columns.dataset_id
        )
    op.get_bind().execute(sql)
    _LOG.debug("Filled uuids in table %r", table.name)
