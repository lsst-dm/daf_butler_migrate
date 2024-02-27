# This file is part of daf_butler_migrate.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import cast

import sqlalchemy
from alembic.runtime.migration import MigrationContext
from lsst.daf.butler import ButlerConfig, RegistryConfig

from . import revision

_LOG = logging.getLogger(__name__)


class RevisionConsistencyError(Exception):
    """Exception raised when butler_attributes and alembic_version tables are
    in inconsistent state
    """


class Database:
    """Class implementing methods for database access needed for migrations.

    Parameters
    ----------
    db_url : `str`
        Database URL.
    schema : `str`, optional
        Database schema/namespace.
    """

    dimensions_json_key = "config:dimensions.json"
    """Key for dimensions configuration in butler_attributes table (`str`)"""

    dimensions_config_manager = "dimensions-config"
    """Name of the special dimensions-config pseudo-manager (`str`)"""

    obscore_json_key = "config:obscore.json"
    """Key for obscore configuration in butler_attributes table (`str`)"""

    obscore_config_manager = "obscore-config"
    """Name of the special obscore-config pseudo-manager (`str`)"""

    def __init__(self, db_url: sqlalchemy.engine.url.URL, schema: str | None = None):
        self._db_url = db_url
        self._schema = schema

    @classmethod
    def from_repo(cls, repo: str) -> Database:
        """Create Database instance from butler repo configuration.

        Parameters
        ----------
        repo : `str`
            Path to butler configuration YAML file or a directory containing a
            "butler.yaml" file.
        """
        butlerConfig = ButlerConfig(repo)
        registryConfig = RegistryConfig(butlerConfig)
        butlerRoot = butlerConfig.get("root", butlerConfig.configDir)
        registryConfig.replaceRoot(butlerRoot)
        db_url = registryConfig.connectionString
        schema = registryConfig.get("namespace")

        _LOG.debug("db_url=%r, schema=%r", db_url, schema)
        return cls(db_url, schema)

    @property
    def db_url(self) -> str:
        """URL for registry database (`str`)"""
        return self._db_url.render_as_string(hide_password=False)

    @property
    def schema(self) -> str | None:
        """Schema (namespace) name (`str`)"""
        return self._schema

    @contextmanager
    def connect(self) -> Iterator[sqlalchemy.engine.Connection]:
        """Context manager for database connection."""
        engine = sqlalchemy.engine.create_engine(self._db_url)
        with engine.connect() as connection:
            yield connection

    def dimensions_namespace(self) -> str | None:
        """Return dimensions namespace from a stored configuration.

        Returns
        -------
        namespace: `str` or `None`
            Dimensions namespace or `None` if not defined.
        """
        engine = sqlalchemy.engine.create_engine(self._db_url)

        meta = sqlalchemy.schema.MetaData(schema=self._schema)
        table = sqlalchemy.schema.Table(
            "butler_attributes",
            meta,
            sqlalchemy.schema.Column("name", sqlalchemy.Text),
            sqlalchemy.schema.Column("value", sqlalchemy.Text),
        )

        sql = sqlalchemy.sql.select(table.columns.value).where(table.columns.name == self.dimensions_json_key)
        with engine.connect() as connection:
            result = connection.execute(sql)
            row = result.fetchone()
            if row is None:
                return None
            dimensions_json = json.loads(row[0])
            return dimensions_json.get("namespace")

    def manager_versions(self, namespace: str | None = None) -> Mapping[str, tuple[str, str, str]]:
        """Retrieve current manager versions stored in butler_attributes table.

        Parameters
        ----------
        namespace : `str`, optional
            Dimensions namespace to use when "namespace" key is not present in
            ``config:dimensions.json``.

        Returns
        -------
        versions : `dict` [ `tuple` ]
            Mapping whose key is manager name (e.g. "datasets") and value is a
            tuple consisting of manager class name (including package/module),
            version string in X.Y.Z format, and revision ID string/hash.
        """
        engine = sqlalchemy.engine.create_engine(self._db_url)

        meta = sqlalchemy.schema.MetaData(schema=self._schema)
        table = sqlalchemy.schema.Table(
            "butler_attributes",
            meta,
            sqlalchemy.schema.Column("name", sqlalchemy.Text),
            sqlalchemy.schema.Column("value", sqlalchemy.Text),
        )

        # parse table contents into two separate maps
        managers: dict[str, str] = {}
        versions: dict[str, str] = {}
        sql = sqlalchemy.sql.select(table.columns.name, table.columns.value)
        with engine.connect() as connection:
            result = connection.execute(sql)
            for name, value in result:
                if name.startswith("config:registry.managers."):
                    managers[name.rpartition(".")[-1]] = value
                elif name.startswith("version:"):
                    versions[name.partition(":")[-1]] = value
                elif name == self.dimensions_json_key:
                    dimensions_json = json.loads(value)
                    namespace = dimensions_json.get("namespace", namespace)
                    # If namespace is missing and not provided with parameters
                    # then don't include pseudo-manager (but CLI will force
                    # parameter use if stored one is missing).
                    if namespace is not None:
                        managers[self.dimensions_config_manager] = namespace
                        versions[namespace] = str(dimensions_json["version"])
                elif name == self.obscore_json_key:
                    obscore_json = json.loads(value)
                    namespace = obscore_json["namespace"]
                    # make unique name to avoid clash with dimensions
                    # namespace, prefix and colon will be dropped below.
                    namespace = f"obscore-config:{namespace}"
                    managers[self.obscore_config_manager] = namespace
                    versions[namespace] = str(obscore_json["version"])

        # combine them into one structure
        revisions: dict[str, tuple[str, str, str]] = {}
        for manager, klass in managers.items():
            version = versions.get(klass)
            if version:
                # drop special prefix
                klass = klass.rpartition(":")[-1]
                # for revision ID we use class name without module
                rev_id_str = revision.rev_id(manager, klass.rpartition(".")[-1], version)
                revisions[manager] = (klass, version, rev_id_str)

        return revisions

    def alembic_revisions(self) -> list[str]:
        """Return a list of current revision numbers from database

        Returns
        -------
        revisions : `list` [ `str` ]
            Returned list is empty if alembic version table does not exist or
            is empty.
        """
        engine = sqlalchemy.engine.create_engine(self._db_url)
        with engine.connect() as connection:
            ctx = MigrationContext.configure(
                connection=connection, opts={"version_table_schema": self._schema}
            )
            return list(ctx.get_current_heads())

    def validate_revisions(
        self, namespace: str | None = None, base_revisions: Iterable[str] | None = None
    ) -> None:
        """Verify consistency of alembic revisions and butler versions.

        Revisions in alembic table must match either a version of a manager in
        butler_attributes or base revision (for manager that did not make yet
        into butler_attributes).

        Parameters
        ----------
        namespace : `str`, optional
            Dimensions namespace to use when "namespace" key is not present in
            ``config:dimensions.json``.
        base_revisions : `iterable` [`str`], optional
            Optional base revisions of the migration trees.

        Raises
        ------
        RevisionConsistencyError
            Raised if contents of the two tables is not consistent. Exception
            message contains details of differences.
        """
        # TODO: possible optimization to reuse a connection to database
        try:
            manager_versions = self.manager_versions(namespace)
        except sqlalchemy.exc.OperationalError:
            raise RevisionConsistencyError("butler_attributes table does not exist")
        alembic_revisions = self.alembic_revisions()

        if manager_versions and not alembic_revisions:
            raise RevisionConsistencyError("alembic_version table does not exist or is empty")
        if alembic_revisions and not manager_versions:
            raise RevisionConsistencyError("butler_attributes table is empty")

        alembic_revs = set(alembic_revisions)
        manager_revs: dict[str, tuple[str, str, str]] = {}
        for manager, (klass, version, rev_id) in sorted(manager_versions.items()):
            manager_revs[rev_id] = (manager, klass, version)
        manager_revs_set = set(manager_revs.keys())

        alembic_only = alembic_revs - manager_revs_set
        if base_revisions:
            alembic_only = alembic_only - set(base_revisions)
        manager_only = manager_revs_set - alembic_revs

        if alembic_only or manager_only:
            msg = "Butler and alembic revisions are inconsistent --"
            sep = ""
            if alembic_only:
                alembic_only_str = ",".join(alembic_only)
                msg += f" revisions in alembic only: {alembic_only_str}"
                sep = ";"
            if manager_only:
                msg += sep + " revisions in butler only:"
                for rev in manager_only:
                    msg += f" {rev}={manager_revs[rev]}"
            raise RevisionConsistencyError(msg)

    def dump_schema(self, tables: list[str] | None) -> None:
        """Dump the schema of the registry database.

        Parameters
        ----------
        tables : `list`, optional
            List of the tables, if missing or empty then schema for all tables
            is printed.
        """
        engine = sqlalchemy.engine.create_engine(self._db_url)
        inspector = sqlalchemy.inspect(engine)
        table_names = sorted(inspector.get_table_names(schema=self._schema))
        for table in table_names:
            if tables and table not in tables:
                continue

            print(f"table={table}")

            column_list = inspector.get_columns(table, schema=self._schema)
            column_list.sort(key=lambda c: c["name"])
            for col in column_list:
                print(
                    f"  column={col['name']} type={col['type']} nullable={col['nullable']}"
                    f" default={col['default']} [table={table}]"
                )

            pk = inspector.get_pk_constraint(table, schema=self._schema)
            if pk:
                columns = ",".join(pk["constrained_columns"])
                print(f"  PK name={pk['name']} columns=({columns}) [table={table}]")

            uniques = inspector.get_unique_constraints(table, schema=self._schema)
            uniques.sort(key=lambda uq: cast(str, uq["name"]))
            for uq in uniques:
                columns = ",".join(uq["column_names"])
                print(f"  UNIQUE name={uq['name']} columns=({columns}) [table={table}]")

            fks = inspector.get_foreign_keys(table, schema=self._schema)
            fks.sort(key=lambda fk: cast(str, fk["name"]))
            for fk in fks:
                columns = ",".join(fk["constrained_columns"])
                ref_columns = ",".join(fk["referred_columns"])
                print(
                    f"  FK name={fk['name']} ({columns}) -> {fk['referred_table']}({ref_columns})"
                    f" [table={table}]"
                )

            checks = inspector.get_check_constraints(table, schema=self._schema)
            checks.sort(key=lambda chk: cast(str, chk["name"]))
            for check in checks:
                print(f"  CHECK name={check['name']} sqltext={check['sqltext']} [table={table}]")

            indices = inspector.get_indexes(table, schema=self._schema)
            indices.sort(key=lambda idx: cast(str, idx["name"]))
            for idx in indices:
                columns = ",".join(cast(list[str], idx["column_names"]))
                print(
                    f"  INDEX name={idx['name']} columns=({columns}) unique={idx['unique']} [table={table}]"
                )
