"""Migration script for dimensions.yaml namespace=daf_butler version=5.

Revision ID: 2a8a32e1bec3
Revises: 9888256c6a18
Create Date: 2024-02-20 14:49:26.435042

"""
import logging

import sqlalchemy
from alembic import context, op
from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

# revision identifiers, used by Alembic.
revision = "2a8a32e1bec3"
down_revision = "9888256c6a18"
branch_labels = None
depends_on = None

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")


def upgrade() -> None:
    """Upgrade from version 4 to version 5 following update of dimension.yaml
    in DM-42896.

    Summary of changes:

        - Length of the ``name`` column in ``instrument`` table changed from
          16 to 32 character.
        - Changes in `config:dimensions.json`:
          - "version" value updated to 5,
          - size of the "name" column for "instrument" element changed to 32.
    """
    _migrate(4, 5, 32)


def downgrade() -> None:
    """Perform schema downgrade."""
    _migrate(5, 4, 16)


def _migrate(old_version: int, new_version: int, size: int) -> None:
    """Perform schema migration.

    Parameters
    ----------
    old_version : `int`
        Current schema version.
    new_version : `int`
        Schema version to migrate to.
    size : `int`
        New size of the name column.
    """

    def _update_config(config: dict) -> dict:
        """Update dimension.json configuration"""
        assert config["version"] == old_version, f"dimensions.json version mismatch: {config['version']}"

        _LOG.info("Update dimensions.json version to %s", new_version)
        config["version"] = new_version

        elements = config["elements"]
        instrument = elements["instrument"]
        for key in instrument["keys"]:
            if key["name"] == "name":
                _LOG.info("Update dimensions.json column size to %s", size)
                key["length"] = size
                break

        return config

    mig_context = context.get_context()

    # When we use schemas in postgres then all tables belong to the same schema
    # so we can use alembic's version_table_schema to see where everything goes
    schema = mig_context.version_table_schema

    # Change table column type.
    new_type = sqlalchemy.String(size)
    _LOG.info("Alter instrument.name column type to %s", new_type)
    op.alter_column("instrument", "name", type_=new_type, schema=schema)

    # Update attributes
    assert mig_context.bind is not None
    attributes = ButlerAttributes(mig_context.bind, schema)
    attributes.update_dimensions_json(_update_config)
