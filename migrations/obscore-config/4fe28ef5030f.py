"""Migration script for obscore-config namespace=embargo version=1.

Revision ID: 4fe28ef5030f
Revises: 2daeabfb5019
Create Date: 2023-02-02 10:28:46.217250

"""

import json

import yaml
from alembic import context, op
from lsst.daf.butler.registry.sql_registry import SqlRegistry
from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes
from lsst.daf.butler_migrate.registry import make_registry
from lsst.utils import doImportType

# revision identifiers, used by Alembic.
revision = "4fe28ef5030f"
down_revision = "2daeabfb5019"
branch_labels = ("obscore-config-embargo",)
depends_on = None

# Namespace, config file must have the same namespace
_NAMESPACE = "embargo"

# Version, config file must have the same version
_VERSION = 1


def upgrade() -> None:
    """Upgrade from "no-config" to version 1.

    Summary of changes for this upgrade:

        - obscore manager has to be defined in the butler_attributes table
        - add "config:obscore.json" key to butler_attributes table

    The script reads obscore configuration from YAML file
    """

    obscore_config = _read_obscore_config()
    _migrate(obscore_config)
    _make_obscore_table(obscore_config)

    print(
        "*** Before anything can be written the upgraded Registry you need to run\n"
        "*** `butler obscore update-table` command (defined in dax_obscore package)."
    )


def downgrade() -> None:
    """Upgrade from version 1 to "no-config".

    Summary of changes for this upgrade:

        - delete "config:obscore.json" key from butler_attributes table
    """

    _migrate(None)

    print(
        "*** Obscore configuration has been removed from butler_attributes,\n"
        "*** but the actual obscore table(s) have to be dropped manually."
    )


def _migrate(obscore_config: dict | None) -> None:
    """Upgrade or downgrade schema."""

    mig_context = context.get_context()
    schema = mig_context.version_table_schema
    bind = op.get_bind()

    attributes = ButlerAttributes(bind, schema)

    # Check the key in butler_attributes.
    obscore_json_key = "config:obscore.json"
    value = attributes.get(obscore_json_key)
    if obscore_config is not None:
        if value is not None:
            raise KeyError(f"Key {obscore_json_key!r} is already defined in butler_attributes.")
    else:
        if value is None:
            raise KeyError(f"Key {obscore_json_key!r} is not defined in butler_attributes.")

    if obscore_config is not None:
        config_str = json.dumps(obscore_config)
        attributes.insert(obscore_json_key, config_str)
    else:
        attributes.delete(obscore_json_key)


def _read_obscore_config() -> dict:
    """Read obscore configuration from YAML file."""

    config = context.config
    obscore_config_path = config.get_section_option("daf_butler_migrate_options", "obscore_config")
    if obscore_config_path is None:
        raise ValueError(
            "This migration script requires an obscore configuration file in YAML format."
            " Please use `--options obscore_config=/path/to/butler.yaml` command line option."
        )

    # Ideally we want to verify YAML file to match obscore configuration, but
    # that means bringing a lot of dependencies here which I do not want to do.
    # So just parse YAML, check required fields and convert to JSON.
    with open(obscore_config_path) as yaml_file:
        obscore_config = yaml.safe_load(yaml_file)

    namespace = obscore_config.get("namespace")
    version = obscore_config.get("version")
    if namespace is None:
        raise ValueError("Namespace is not defined in configuration file")
    if namespace != _NAMESPACE:
        raise ValueError(
            f"Namespace defined in configuration file ({namespace}) "
            f"does not match expected namespace {_NAMESPACE}"
        )
    if version is None:
        raise ValueError("Version is not defined in configuration file")
    if version != _VERSION:
        raise ValueError(
            f"Version defined in configuration file ({version}) "
            f"does not match expected version {_VERSION}"
        )

    return obscore_config


def _make_obscore_table(obscore_config: dict) -> None:
    """Create obecore table."""

    mig_context = context.get_context()
    schema = mig_context.version_table_schema
    bind = op.get_bind()

    attributes = ButlerAttributes(bind, schema)

    # We have to create actual obscore table, and using the manager is the
    # only reasonable way to do it.
    manager_class_name = attributes.get("config:registry.managers.obscore")
    if manager_class_name is None:
        raise ValueError("Registry obscore manager has to be configured in butler_attributes")
    manager_class = doImportType(manager_class_name)

    repository = context.config.get_section_option("daf_butler_migrate", "repository")
    assert repository is not None, "Need repository in configuration"
    registry = make_registry(repository)
    assert isinstance(registry, SqlRegistry), "Can only work with SQL registry"  # for mypy

    # Registry has no interface for creating table for just one manager, so
    # here is a hackish way to do it which depends on knowing internals.
    database = registry._db
    managers = registry._managers
    with database.declareStaticTables(create=False) as staticTablesContext:
        manager = manager_class.initialize(
            database,
            staticTablesContext,
            universe=registry.dimensions,
            config=obscore_config,
            datasets=managers.datasets.__class__,
            dimensions=managers.dimensions,
        )
    # Note that we are using bind from migration context, and not from
    # Registry. This should work in general, but watch for any surprises.
    # Reflecting metadata is needed for foreign key in obscore table.
    assert database._metadata is not None
    database._metadata.reflect(bind, schema=schema)
    manager.table.create(bind)
