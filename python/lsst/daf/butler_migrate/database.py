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
from typing import Dict, List, Mapping, Optional, Tuple

import sqlalchemy
from alembic.runtime.migration import MigrationContext
from lsst.daf.butler import ButlerConfig
from lsst.daf.butler.core.repoRelocation import replaceRoot

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

    def __init__(self, db_url: str, schema: Optional[str] = None):
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
        if "root" in butlerConfig:
            butlerRoot = butlerConfig["root"]
        else:
            butlerRoot = butlerConfig.configDir
        db_url = replaceRoot(butlerConfig["registry", "db"], butlerRoot)
        schema: Optional[str] = None
        try:
            schema = butlerConfig["registry", "namespace"]
        except KeyError:
            pass

        _LOG.debug("db_url=%r, schema=%r", db_url, schema)
        return cls(db_url, schema)

    @property
    def db_url(self) -> str:
        """URL for registry database (`str`)"""
        return self._db_url

    @property
    def schema(self) -> Optional[str]:
        """Schema (namespace) name (`str`)"""
        return self._schema

    def dimensions_namespace(self) -> Optional[str]:
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

    def manager_versions(self, namespace: Optional[str] = None) -> Mapping[str, Tuple[str, str, str]]:
        """Retrieve current manager versions stored in butler_attributes table.

        Parameters
        ----------
        namespace: `str`, optional
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
        managers: Dict[str, str] = {}
        versions: Dict[str, str] = {}
        sql = sqlalchemy.sql.select([table.columns.name, table.columns.value])
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

        # combine them into one structure
        revisions: Dict[str, Tuple[str, str, str]] = {}
        for manager, klass in managers.items():
            version = versions.get(klass)
            if version:
                # for revision ID we use class name without module
                rev_id_str = revision.rev_id(manager, klass.rpartition(".")[-1], version)
                revisions[manager] = (klass, version, rev_id_str)

        return revisions

    def alembic_revisions(self) -> List[str]:
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

    def validate_revisions(self, namespace: Optional[str] = None) -> None:
        """Verify that consistency of alembic revisions and butler versions.

        Parameters
        ----------
        namespace: `str`, optional
            Dimensions namespace to use when "namespace" key is not present in
            ``config:dimensions.json``.

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
        manager_revs: Dict[str, Tuple[str, str, str]] = {}
        for manager, (klass, version, rev_id) in sorted(manager_versions.items()):
            manager_revs[rev_id] = (manager, klass, version)
        manager_revs_set = set(manager_revs.keys())

        if alembic_revs != manager_revs_set:
            msg = "Butler and alembic revisions are inconsistent --"
            alembic_only = alembic_revs - manager_revs_set
            manager_only = manager_revs_set - alembic_revs
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
