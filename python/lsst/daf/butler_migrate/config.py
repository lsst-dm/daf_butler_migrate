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
import os
from typing import Any

from alembic.config import Config

from . import database, migrate

_LOG = logging.getLogger(__name__)

_MIGRATE_PACKAGE_ENV = "DAF_BUTLER_MIGRATE_DIR"


class MigAlembicConfig(Config):
    """Implementation of alembic config class which overrides few methods."""

    @classmethod
    def from_mig_path(
        cls,
        mig_path: str,
        *args: Any,
        repository: str | None = None,
        db: database.Database | None = None,
        single_tree: str | None = None,
        one_shot_tree: str | None = None,
        migration_options: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> MigAlembicConfig:
        """Create new configuration object.

        Parameters
        ----------
        mig_path : `str`
            Filesystem path to location of revision trees.
        repository : `str`
            Path to repository configuration file.
        db : `database.Database`
            Object encapsulating access to database information.
        single_tree : `str`, optional
            If provided then Alembic will be configured with a single version
            tree only. If it contains slash charater then it is assumed to be
            one-shot tree.
        one_shot_tree : `str`, optional
            If this is given (and ``single_tree`` is not) then this tree will
            replace regular version tree for corresponding manager. Tree name
            must contain slash character separating manager name and tree name.
        migration_options : `dict`, optional
            Additional options that can be passed to migration script via the
            configuration object, in a section "daf_butler_migrate_options".
        """
        alembic_folder = os.path.join(mig_path, "_alembic")
        ini_path = os.path.join(alembic_folder, "alembic.ini")
        cfg = cls(ini_path, *args, **kwargs)
        cfg.set_main_option("script_location", alembic_folder)

        _LOG.debug(
            "alembic_folder: %r, single_tree: %r, one_shot_tree: %r",
            alembic_folder,
            single_tree,
            one_shot_tree,
        )

        migrate_trees = migrate.MigrationTrees(mig_path)
        if single_tree:
            if "/" in single_tree:
                # means one-shot tree
                version_locations = [migrate_trees.one_shot_version_location(single_tree, relative=False)]
            else:
                version_locations = [migrate_trees.regular_version_location(single_tree, relative=False)]
        else:
            version_locations = migrate_trees.version_locations(one_shot_tree, relative=False)
        _LOG.debug("version_locations: %r", version_locations)
        cfg.set_main_option("version_locations", " ".join(version_locations))

        # override default file template
        cfg.set_main_option("file_template", "%%(rev)s")

        # we do not use this option, this is just to make sure that
        # [daf_butler_migrate] section exists
        cfg.set_section_option("daf_butler_migrate", "_daf_butler_migrate", "")
        cfg.set_section_option("daf_butler_migrate_options", "_daf_butler_migrate_options", "")

        if repository is not None:
            cfg.set_section_option("daf_butler_migrate", "repository", repository)

        if db is not None:
            # URL may contain URL-encoded items which include % sign, and that
            # needs to be escaped with another % before it is passed to
            # ConfigParser.
            url = db.db_url.replace("%", "%%")
            cfg.set_main_option("sqlalchemy.url", url)
            if db.schema:
                cfg.set_section_option("daf_butler_migrate", "schema", db.schema)

        if migration_options:
            for key, value in migration_options.items():
                cfg.set_section_option("daf_butler_migrate_options", key, value)

        return cfg

    def get_template_directory(self) -> str:
        """Return the directory where Alembic setup templates are found.

        This overrides method from alembic Config to copy templates for our own
        location.
        """
        package_dir = os.environ.get(_MIGRATE_PACKAGE_ENV)
        if not package_dir:
            raise ValueError(f"{_MIGRATE_PACKAGE_ENV} environment variable is not defined")

        return os.path.join(package_dir, "templates")
