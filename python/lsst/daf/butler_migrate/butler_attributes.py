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

from typing import Optional

import sqlalchemy


class ButlerAttributes:
    """Helper class implementing updates for butler_attributes table.

    Parameters
    ----------
    connection : `sqlalchemy.engine.Connection`
        Database connection.
    schema : str, optional
        Schema name or `None`.
    """

    def __init__(self, connection: sqlalchemy.engine.Connection, schema: Optional[str] = None):
        self._connection = connection
        metadata = sqlalchemy.schema.MetaData(connection, schema=schema)
        self._table = sqlalchemy.schema.Table(
            "butler_attributes", metadata, autoload_with=connection, schema=schema
        )

    def update(self, name: str, value: str) -> int:
        """Update the value of existing parameter in butler_attributes table.

        Parameters
        ----------
        name : `str`
            Attribute name.
        value : `str`
            New attribute value.

        Returns
        -------
        updates : `int`
            Number of updated rows, 0 if no matching attribute found, 1
            otherwise.
        """
        # update version
        sql = self._table.update().where(self._table.columns.name == name).values(value=value)
        return self._connection.execute(sql).rowcount
