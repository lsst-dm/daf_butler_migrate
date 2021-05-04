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
from typing import Any, Optional

from alembic.config import Config

from . import smig


_LOG = logging.getLogger(__name__.partition(".")[2])

_SMIG_PACKAGE_ENV = "DAF_BUTLER_SMIG_DIR"


class SmigAlembicConfig(Config):
    """Implementation of alembic config class which overrides few methods.
    """

    @classmethod
    def from_mig_path(cls, mig_path: str, *args: Any,
                      single_tree: Optional[str] = None,
                      one_shot_tree: Optional[str] = None,
                      **kwargs: Any) -> SmigAlembicConfig:
        """Create new configuration object.

        Parameters
        ----------
        mig_path : `str`
            Filesystem path to location of revision trees.
        single_tree : `str`, optional
            If provided then Alembic will be configured with a single version
            tree only. If it contains slash charater then it is assumed to be
            one-shot tree.
        one_shot_tree : `str`, optional
            If this is given (and ``single_tree`` is not) then this tree will
            replace regular version tree for corresponding manager. Tree name
            must contain slash character separating manager name and tree name.
        """
        alembic_folder = os.path.join(mig_path, "_alembic")
        ini_path = os.path.join(alembic_folder, "alembic.ini")
        cfg = cls(ini_path, *args, **kwargs)
        cfg.set_main_option("script_location", alembic_folder)

        smig_trees = smig.SmigTrees(mig_path)
        if single_tree:
            if "/" in single_tree:
                # means one-shot tree
                version_locations = [smig_trees.one_shot_version_location(single_tree, relative=False)]
            else:
                version_locations = [smig_trees.regular_version_location(single_tree, relative=False)]
        else:
            version_locations = smig_trees.version_locations(one_shot_tree, relative=False)
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
