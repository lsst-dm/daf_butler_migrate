"""Migration script for DefaultButlerAttributeManager 1.0.1.

Revision ID: c0e4f9ab4a5d
Revises: f22a777cf382
Create Date: 2023-03-21 16:38:41.523277

"""
import logging

from alembic import context

from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

# revision identifiers, used by Alembic.
revision = "c0e4f9ab4a5d"
down_revision = "f22a777cf382"
branch_labels = None
depends_on = None

_LOG = logging.getLogger(f"lsst.daf.butler_migrate.{__name__}")

# Manager name
MANAGER = "lsst.daf.butler.registry.attributes.DefaultButlerAttributeManager"


def upgrade() -> None:
    """Upgrade from version 1.0.0 to version 1.0.1.

    There is no actual schema change, only contents of the butler_attributes
    table is updated by removing schema digests for all managers.
    """
    mig_context = context.get_context()

    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes.
    schema = mig_context.version_table_schema

    assert mig_context.bind is not None
    attributes = ButlerAttributes(mig_context.bind, schema)

    # Simple way to do it is to drop all attributes whose name starts with
    # "schema_digest:", but to avoid any potential conflicts I instead
    # iterate over manager names and delete their specific digests.
    items = list(attributes.items())
    count = sum(1 for key, _ in items if key.startswith("schema_digest:"))
    _LOG.info("number of schema digests in table before migration: %s", count)

    for key, value in items:
        if key.startswith("config:registry.managers."):
            digest_name = f"schema_digest:{value}"
            count = attributes.delete(digest_name)
            if count:
                _LOG.info("deleted schema digest for %s", value)
            else:
                _LOG.info("schema digest does not exist for %s", value)

    count = sum(1 for key, _ in attributes.items() if key.startswith("schema_digest:"))
    _LOG.info("number of schema digests in table after migration: %s", count)

    attributes.update_manager_version(MANAGER, "1.0.1")


def downgrade() -> None:
    raise NotImplementedError()
