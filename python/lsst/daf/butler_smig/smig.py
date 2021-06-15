# This file is part of daf_butler_smig.
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

import os
import uuid
from typing import Dict, List, Mapping, Tuple, Optional

import sqlalchemy

from lsst.daf.butler import ButlerConfig
from lsst.daf.butler.core.repoRelocation import replaceRoot


NS_UUID = uuid.UUID('840b31d9-05cd-5161-b2c8-00d32b280d0f')
"""Namespace UUID used for UUID5 generation. Do not change. This was
produced by `uuid.uuid5(uuid.NAMESPACE_DNS, "lsst.org")`.
"""


class SmigTrees:
    """Class encapsulating the knowledge of directory structures used by smig.

    Parameters
    ----------
    mig_path : `str`
        Top-level folder with migrations.
    one_shot : `bool`
        If `True` return locations for special one-shot migrations.
    """

    _MIG_FOLDER_ENV = "DAF_BUTLER_SMIG_MIGRATIONS"
    """Name of envvar that can be used to override location of top-level
    migrations folder.
    """

    _SMIG_PACKAGE_ENV = "DAF_BUTLER_SMIG_DIR"
    """Name of envvar for location of a package containing default migrations.
    """

    def __init__(self, mig_path: Optional[str] = None):
        if mig_path is None:
            self.mig_path = self.migrations_folder()
        else:
            self.mig_path = mig_path

    @classmethod
    def migrations_folder(cls) -> str:
        """Return default location of top-level folder containing all
        migrations.

        Returns
        -------
        path : `str`
            Location of top-level folder containing all migrations.
        """
        loc = os.environ.get(cls._MIG_FOLDER_ENV)
        if loc:
            return loc
        loc = os.environ.get(cls._SMIG_PACKAGE_ENV)
        if loc:
            return os.path.join(loc, "migrations")
        raise ValueError(f"None of {cls._MIG_FOLDER_ENV} or {cls._SMIG_PACKAGE_ENV}"
                         " environment variables is defined")

    def alembic_folder(self, *, relative: bool = True) -> str:
        """Return location of folder with alembic files.

        Parameters
        ----------
        relative : `bool`
            If True (default) then path relative to top-level folder is
            returned.

        Returns
        -------
        path : `str`
            Path to a folder alembic files (env.py, etc.) will be stored, path
            may not exist yet.
        """
        path = "_alembic"
        if not relative:
            path = os.path.join(self.mig_path, path)
        return path

    def regular_version_location(self, manager: str, *, relative: bool = True) -> str:
        """Return location for regular migrations for a given manager.

        Parameters
        ----------
        manager : `str`
            Manager name (e.g. "datasets").
        relative : `bool`
            If True (default) then path relative to top-level folder is
            returned.

        Returns
        -------
        path : `str`
            Path to a folder where migration scripts will be stored, path may
            not exist yet.
        """
        path = manager
        if not relative:
            path = os.path.join(self.mig_path, path)
        return path

    def one_shot_version_location(self, one_shot_tree: str, *, relative: bool = True) -> str:
        """Return location for one-shot migrations for a given manager.

        Parameters
        ----------
        one_shot_tree : `str`
            Name of a special one-shot tree, contains manager name and tree
            name separated by slash.
        relative : `bool`
            If True (default) then path relative to top-level folder is
            returned.

        Returns
        -------
        path : `str`
            Path to a folder where migration scripts will be stored, path may
            not exist yet.
        """
        manager, _, tree_name = one_shot_tree.partition("/")
        if not tree_name:
            raise ValueError("one-shot tree name is missing slash: f{one_shot_tree}")
        path = os.path.join("_oneshot", manager, tree_name)
        if not relative:
            path = os.path.join(self.mig_path, path)
        return path

    def regular_version_locations(self, *, relative: bool = True) -> Dict[str, str]:
        """Return locations for regular migrations.

        Parameters
        ----------
        relative : `bool`
            If True (default) then locations relative to top-level folder are
            returned.

        Returns
        -------
        names : `dict` [ `str`, `str` ]
            Dictionary where key is a manager name (e.g. "datasets") and value
            is the location of a folder with migration scripts.
        """
        locations: Dict[str, str] = {}
        for entry in os.scandir(self.mig_path):
            if entry.is_dir() and entry.name not in ("_alembic", "_oneshot"):
                path = entry.name
                if not relative:
                    path = os.path.join(self.mig_path, path)
                locations[entry.name] = path
        return locations

    def one_shot_locations(self, manager: Optional[str] = None, *, relative: bool = True) -> Dict[str, str]:
        """Return locations for one-shot migrations for specific manager.

        Parameters
        ----------
        manager : `str`
            Manager name (e.g. "datasets").
        relative : `bool`
            If True (default) then locations relative to top-level folder are
            returned.

        Returns
        -------
        names : `dict` [ `str`, `os.DirEntry` ]
            Dictionary where key is a one-shot tree name and value is the
            location of a folder with migration scripts.
        """
        locations: Dict[str, str] = {}

        one_shot_loc = os.path.join(self.mig_path, "_oneshot")
        if not os.access(one_shot_loc, os.F_OK):
            return locations

        if manager:
            managers = [manager]
        else:
            managers = [entry.name for entry in os.scandir(one_shot_loc) if entry.is_dir()]

        for manager in managers:
            rel_path = os.path.join("_oneshot", manager)
            manager_path = os.path.join(self.mig_path, rel_path)
            # it may not exist, treat it as empty
            if not os.access(manager_path, os.F_OK):
                continue
            for entry in os.scandir(manager_path):
                if entry.is_dir():
                    path = os.path.join(rel_path, entry.name)
                    if not relative:
                        path = os.path.join(self.mig_path, path)
                    locations[manager + "/" + entry.name] = path
        return locations

    def version_locations(self, one_shot_tree: Optional[str] = None, *, relative: bool = True) -> List[str]:
        """Return list of folders for version_locations.

        Parameters
        ----------
        one_shot_tree : `str`, optional
            Name of a special one-shot tree to use instead of default tree for
            corresponding manager, , contains manager name and tree name
            separated by slash.
        relative : `bool`
            If True (default) then locations relative to top-level folder are
            returned.

        Returns
        -------
        names : `list` [ `str` ]
            String containing space-separated list of locations.
        """
        locations = self.regular_version_locations(relative=relative)
        if one_shot_tree:
            manager, _, tree_name = one_shot_tree.partition("/")
            if not tree_name:
                raise ValueError("one-shot tree name is missing slash: f{one_shot_tree}")
            locations[manager] = self.one_shot_version_location(one_shot_tree, relative=relative)
        return list(locations.values())


def rev_id(*args: str) -> str:
    """Generate revision ID from arguments.

    Returned string is a determenistic hash of the arguments.

    Returns
    -------
    rev_id : `str`
        Revision ID, 12-character string.
    """
    name = "-".join(args)
    return uuid.uuid5(NS_UUID, name).hex[-12:]


def butler_db_url(repo: str) -> str:
    """Extract registry database URL from Butler configuration.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.

    Returns
    -------
    db_url : `str`
        URL for registry database.
    """
    butlerConfig = ButlerConfig(repo)
    if "root" in butlerConfig:
        butlerRoot = butlerConfig["root"]
    else:
        butlerRoot = butlerConfig.configDir
    db_url = replaceRoot(butlerConfig["registry", "db"], butlerRoot)

    return db_url


def manager_versions(db_url: str) -> Mapping[str, Tuple[str, str]]:
    """Retrieve current manager versions stored in butler_attributes table.

    Parameters
    ----------
    db_url : `str`
        URL for registry database.

    Returns
    -------
    versions : `dict` [ `tuple` ]
        Mapping whose key is manager name (e.g. "datasets") and value is a
        tuple consisting of manager class name (including package/module) and
        version in X.Y.Z format.
    """
    engine = sqlalchemy.engine.create_engine(db_url)

    meta = sqlalchemy.schema.MetaData()
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
    revisions: Dict[str, Tuple[str, str]] = {}
    for manager, klass in managers.items():
        version = versions.get(klass)
        if version:
            revisions[manager] = (klass, version)

    return revisions
