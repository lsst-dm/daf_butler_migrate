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

from lsst.daf.butler.registry.sql_registry import SqlRegistry


def make_registry(repository: str, writeable: bool = True) -> SqlRegistry:
    """Make Registry instance.

    Parameters
    ----------
    repository : `str`
        Path to Butler repository configuration file.
    writeable : `bool`, optional
        If `True` (default) create a read-write connection to the database.
    """
    return SqlRegistry.fromConfig(config=repository, writeable=writeable)
