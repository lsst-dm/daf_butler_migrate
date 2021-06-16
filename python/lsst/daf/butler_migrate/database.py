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

import logging
from typing import Dict, Mapping, Tuple, Optional

import sqlalchemy

from . import revision
from lsst.daf.butler import ButlerConfig
from lsst.daf.butler.core.repoRelocation import replaceRoot


_LOG = logging.getLogger(__name__)


class Database:
    """Class implementing methods for database access needed for migrations.

    Parameters
    ----------
    db_url : `str`
        Database URL.
    schema : `str`, optional
        Database schema/namespace.
    """
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

    def manager_versions(self) -> Mapping[str, Tuple[str, str, str]]:
        """Retrieve current manager versions stored in butler_attributes table.

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
            "butler_attributes", meta,
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

        # combine them into one structure
        revisions: Dict[str, Tuple[str, str, str]] = {}
        for manager, klass in managers.items():
            version = versions.get(klass)
            if version:
                # for revision ID we use class name without module
                rev_id_str = revision.rev_id(manager, klass.rpartition(".")[-1], version)
                revisions[manager] = (klass, version, rev_id_str)

        return revisions
