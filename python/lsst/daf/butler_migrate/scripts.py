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

from alembic.config import Config
from alembic.script import ScriptDirectory


class Scripts:
    """Class that provides convenience methods for obtaining information about
    migration scripts.

    Parameters
    ----------
    config : `alembic.config.Config`
        Alembic configuration.
    """

    def __init__(self, config: Config):
        self.scripts = ScriptDirectory.from_config(config)

    def base_revisions(self) -> list[str]:
        """Return list of all base revisions, or roots of the migration trees.

        Returns
        -------
        bases : `list` [`str`]
            Base revisions, corresponding to the roots of the each manager
            migration tree.
        """
        return list(self.scripts.get_bases())

    def head_revisions(self) -> list[str]:
        """Return list of all head revisions, or tops of the migration trees.

        Returns
        -------
        heads : `list` [`str`]
            Head revisions, corresponding to the tops of the each migration
            tree.
        """
        return list(self.scripts.get_heads())
