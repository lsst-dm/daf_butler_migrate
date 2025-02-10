"""Migration script for ObsCoreLiveTableManager 0.0.1.

Revision ID: a0d766f99876
Revises: 8b8e030aba2b
Create Date: 2022-10-27 16:05:17.523936

"""

from alembic import context, op

from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

# revision identifiers, used by Alembic.
revision = "a0d766f99876"
down_revision = "8b8e030aba2b"
branch_labels = ("obscore-ObsCoreLiveTableManager",)
depends_on = None

# butler_attributes key for obscore
OBSCORE_CONFIG_KEY = "config:registry.managers.obscore"

# Manager name
MANAGER = "lsst.daf.butler.registry.obscore._manager.ObsCoreLiveTableManager"

# Version string
MANAGER_VERSION = "0.0.1"


def upgrade() -> None:
    """Summary of changes for this migration:

        - add obscore manager entry to butler_attributes table.

    Notes
    -----
    This migration has to be used together with ``obscore-config`` migration
    script which creates actual obscore table.
    """
    _migrate(upgrade=True)

    print(
        "*** Do not forget to add this line to butler.yaml file (registry.managers):\n"
        f"***     obscore: {MANAGER}"
    )


def downgrade() -> None:
    """Summary of changes for this migration:

        - remove obscore manager entry from butler_attributes table.

    Notes
    -----
    This migration has to be used together with ``obscore-config`` migration
    script which should remove actual obscore table.
    """
    _migrate(upgrade=False)


def _migrate(upgrade: bool) -> None:
    """Upgrade or downgrade schema."""

    mig_context = context.get_context()
    schema = mig_context.version_table_schema
    bind = op.get_bind()

    attributes = ButlerAttributes(bind, schema)
    version_key = f"version:{MANAGER}"

    # Check the keys in butler_attributes.
    for key in (OBSCORE_CONFIG_KEY, version_key):
        value = attributes.get(key)
        if upgrade:
            if value is not None:
                raise KeyError(f"Key {key!r} is already defined in butler_attributes.")
        else:
            if value is None:
                raise KeyError(f"Key {key!r} is not defined in butler_attributes.")

    if upgrade:
        attributes.insert(OBSCORE_CONFIG_KEY, MANAGER)
        attributes.insert(version_key, MANAGER_VERSION)
    else:
        attributes.delete(OBSCORE_CONFIG_KEY)
        attributes.delete(version_key)
