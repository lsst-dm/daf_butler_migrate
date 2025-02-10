"""Migration script for StaticDimensionRecordStorageManager 6.0.1.

Revision ID: 1601d5973bf8
Revises: 87a30df8c8c5
Create Date: 2021-09-01 09:43:25.448091

"""
import sqlalchemy as sa
from alembic import context, op

from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes
from lsst.daf.butler_migrate.shrink import shrinkDatabaseEntityName

# revision identifiers, used by Alembic.
revision = "1601d5973bf8"
down_revision = "87a30df8c8c5"
branch_labels = None
depends_on = None


# maps table name to columns in new index
INDICES = {
    "patch_skypix_overlap": ["skypix_system", "skypix_level", "skypix_index", "skymap", "tract", "patch"],
    "tract_skypix_overlap": ["skypix_system", "skypix_level", "skypix_index", "skymap", "tract"],
    "visit_detector_region_skypix_overlap": [
        "skypix_system",
        "skypix_level",
        "skypix_index",
        "instrument",
        "detector",
        "visit",
    ],
    "visit_skypix_overlap": ["skypix_system", "skypix_level", "skypix_index", "instrument", "visit"],
}

# Manager name
MANAGER = "lsst.daf.butler.registry.dimensions.static.StaticDimensionRecordStorageManager"


def upgrade() -> None:
    """Upgrade from StaticDimensionRecordStorageManager 6.0.0 to 6.0.1"""
    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes
    mig_context = context.get_context()
    schema = mig_context.version_table_schema

    # Shrinking of index names depends on dialect, caveat here is that offline
    # migration is virtually impossible in this case.
    bind = op.get_bind()

    for table_name, columns in INDICES.items():
        index_name = "_".join([table_name, "idx"] + columns)
        index_name = shrinkDatabaseEntityName(index_name, bind)
        op.create_index(index_name, table_name, columns, schema=schema)

    attributes = ButlerAttributes(bind, schema)
    attributes.update_manager_version(MANAGER, "6.0.1")


def downgrade() -> None:
    """Downgrade from StaticDimensionRecordStorageManager 6.0.1 to 6.0.0"""
    mig_context = context.get_context()
    schema = mig_context.version_table_schema
    bind = op.get_bind()

    for table_name, columns in INDICES.items():
        index_name = "_".join([table_name, "idx"] + columns)
        index_name = shrinkDatabaseEntityName(index_name, bind)
        op.drop_index(index_name, table_name, schema=schema)

    attributes = ButlerAttributes(bind, schema)
    attributes.update_manager_version(MANAGER, "6.0.0")
