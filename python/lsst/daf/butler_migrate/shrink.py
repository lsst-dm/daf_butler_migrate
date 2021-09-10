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

import sqlalchemy

from lsst.daf.butler.registry.nameShrinker import NameShrinker


def shrinkDatabaseEntityName(original: str, connection: sqlalchemy.engine.Connection) -> str:
    """Shrink database entity name to a maximum allowed length.

    Parameters
    ----------
    original : `str`
        Full name of an entity.
    connection : `sqlalchemy.engine.Connection`
        Database connection.

    Returns
    -------
    shrinked : `str`
        Possibly shrinked entity name.

    Notes
    -----
    As we do not want to instantiate ``Database`` from `daf_butler` here we
    need to re-implement part of the behavior here. For now we know that
    shrinking is only needed for Postgres and we use ``NameShrinker`` class
    to do actual work in that case.
    """
    dialect = connection.dialect
    if dialect.name == "postgresql":
        shrinker = NameShrinker(dialect.max_identifier_length)
        return shrinker.shrink(original)

    return original
