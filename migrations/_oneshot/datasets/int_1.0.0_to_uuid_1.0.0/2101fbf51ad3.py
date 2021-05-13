"""Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.

Revision ID: 2101fbf51ad3
Revises: 635083325f20
Create Date: 2021-05-04 16:31:05.926989

"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '2101fbf51ad3'
down_revision = '635083325f20'
branch_labels = None
depends_on = None


_LOG = logging.getLogger(__name__)

def upgrade():
    """Change type of the primary key colum in dataset table from int to UUID.

    This is a rather complicated migration, and here is the list of changes
    that we need to do:

    - PK column on dataset table changes from int to uuid (native uuid type
      in Postgres, CHAR(32) in sqlite).
    - The value of the column needs to be generated on Python, it is either
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
    _LOG.debug("dialect: %r", dialect)

    # reflect schema from database
    metadata = sa.schema.MetaData(bind, reflect=True)

    # get dataset table
    dataset_table = metadata.tables["dataset"]
    assert len(dataset_table.primary_key) == 1
    assert dataset_table.primary_key.columns["id"] is not None

    # find all tables and columns that reference dataset.id
    reftables = _referencing_tables(dataset_table, metadata)

    # need to know data type for new UUID column, this is dialect-specific
    if dialect.name == 'postgresql':
        uuid_type = dialect.type_descriptor(UUID())
    else:
        uuid_type = dialect.type_descriptor(sa.CHAR(32))
    _LOG.debug("uuid_type: %r", uuid_type)

    # create columns for each referencing table
    for table, (fk_name, column) in reftables.items():
        new_column_name = "_new_" + column

        _LOG.debug("referencing table.column: %s.%s key_name=%r", table, column, fk_name)

    raise NotImplementedError()


def downgrade():
    raise NotImplementedError()


def _referencing_tables(dataset_table: sa.schema.Table, metadata: sa.schema.MetaData
                        ) -> Dict[str, Tuple[Optional[str], str]]:

    # find all tables and columns that reference dataset.id
    tables: Dict[str, Tuple[Optional[str], str]] = {}
    for table_name, table in metadata.tables.items():
        for fk in table.foreign_key_constraints:
            if fk.referred_table is dataset_table:
                assert len(fk.column_keys) == 1
                tables[table.name] = (fk.name, fk.column_keys[0])

    # dataset_location_trash is the same as dataset_location but without FK
    if "dataset_location" in tables and "dataset_location_trash" not in tables:
        tables["dataset_location_trash"] = (None, tables["dataset_location"][1])

    for table, (fk_name, column) in tables.items():
        _LOG.debug("referencing table.column: %s.%s key_name=%r", table, column, fk_name)

    return tables
