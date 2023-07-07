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

import os


class MigrationTrees:
    """Class encapsulating the knowledge of directory structures used by
    migrations.

    Parameters
    ----------
    mig_path : `str`
        Top-level folder with migrations.
    """

    _MIGRATE_FOLDER_ENV = "DAF_BUTLER_MIGRATE_MIGRATIONS"
    """Name of envvar that can be used to override location of top-level
    migrations folder.
    """

    _MIGRATE_PACKAGE_ENV = "DAF_BUTLER_MIGRATE_DIR"
    """Name of envvar for location of a package containing default migrations.
    """

    def __init__(self, mig_path: str | None = None):
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
        loc = os.environ.get(cls._MIGRATE_FOLDER_ENV)
        if loc:
            return loc
        loc = os.environ.get(cls._MIGRATE_PACKAGE_ENV)
        if loc:
            return os.path.join(loc, "migrations")
        raise ValueError(
            f"None of {cls._MIGRATE_FOLDER_ENV} or {cls._MIGRATE_PACKAGE_ENV}"
            " environment variables is defined"
        )

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

    def regular_version_locations(self, *, relative: bool = True) -> dict[str, str]:
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
        locations: dict[str, str] = {}
        for entry in os.scandir(self.mig_path):
            if entry.is_dir() and entry.name not in ("_alembic", "_oneshot"):
                path = entry.name
                if not relative:
                    path = os.path.join(self.mig_path, path)
                locations[entry.name] = path
        return locations

    def one_shot_locations(self, manager: str | None = None, *, relative: bool = True) -> dict[str, str]:
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
        locations: dict[str, str] = {}

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

    def version_locations(self, one_shot_tree: str | None = None, *, relative: bool = True) -> list[str]:
        """Return list of folders for version_locations.

        Parameters
        ----------
        one_shot_tree : `str`, optional
            Name of a special one-shot tree to use instead of default tree for
            corresponding manager, contains manager name and tree name
            separated by slash.
        relative : `bool`
            If True (default) then locations relative to top-level folder are
            returned.

        Returns
        -------
        names : `list` [ `str` ]
            List of folder names.
        """
        locations = self.regular_version_locations(relative=relative)
        if one_shot_tree:
            manager, _, tree_name = one_shot_tree.partition("/")
            if not tree_name:
                raise ValueError("one-shot tree name is missing slash: f{one_shot_tree}")
            locations[manager] = self.one_shot_version_location(one_shot_tree, relative=relative)
        return list(locations.values())
