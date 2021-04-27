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

import logging
import os
from typing import Any

from alembic.config import Config

from . import smig


_LOG = logging.getLogger(__name__.partition(".")[2])

_SMIG_PACKAGE_ENV = "DAF_BUTLER_SMIG_DIR"


class SmigAlembicConfig(Config):
    """Implementation of alembic config class which overrides few methods.
    """

    @classmethod
    def from_mig_path(cls, mig_path: str, *args: Any,
                      extra_tree_name: str = "", one_shot: bool = False,
                      **kwargs: Any) -> SmigAlembicConfig:
        """Create new configuration object.

        Parameters
        ----------
        mig_path : `str`
            Filesystem path to location of revision trees.
        """
        cfg = cls(*args, **kwargs)
        alembic_folder = os.path.join(mig_path, "_alembic")
        cfg.set_main_option("script_location", alembic_folder)

        version_locations = smig.version_locations(mig_path, one_shot)
        if extra_tree_name:
            version_locations.append(os.path.join(mig_path, extra_tree_name))
        _LOG.debug("version_locations: %r", version_locations)
        cfg.set_main_option("version_locations", " ".join(version_locations))

        # override default file template
        cfg.set_main_option("file_template", "%%(rev)s")

        return cfg

    def get_template_directory(self):
        """Return the directory where Alembic setup templates are found.

        This overrides method from alembic Config to copy templates for our own
        location.
        """
        package_dir = os.environ.get(_SMIG_PACKAGE_ENV)
        if not package_dir:
            raise ValueError(f"{_SMIG_PACKAGE_ENV} environment variables is not defined")

        return os.path.join(package_dir, "templates")
