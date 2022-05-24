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

import json
from typing import Any, Callable, Dict, Optional

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

    def get(self, name: str) -> Optional[str]:
        """Retrieve values of the named attribute.

        Parameters
        ----------
        name : `str`
            Attribute name.

        Returns
        -------
        value : `str` or `None`
            Attribute value, `None` is returned if attribute does not exist.
        """
        sql = sqlalchemy.select(self._table.columns["value"]).where(self._table.columns["name"] == name)
        result = self._connection.execute(sql)
        row = result.fetchone()
        return row[0] if row is not None else None

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

    def get_dimensions_json(self) -> Dict[str, Any]:
        """Return dimensions configuration from dimensions.json.

        Returns
        -------
        config : `dict`
            Contents of ``dimensions.json`` as dictionary.
        """
        key = "config:dimensions.json"
        config_json = self.get(key)
        if config_json is None:
            raise LookupError(f"Key {key} does not exist in attributes table")
        config = json.loads(config_json)
        return config

    def update_dimensions_json(self, update_config: Callable[[Dict], Dict]) -> None:
        """Updates dimensions definitions in dimensions.json.

        Parameters
        ----------
        update_config : `Callable`
            A method that takes a dictionary representation of the
            ``dimensions.json`` and returns an updated dictionary.
        """
        key = "config:dimensions.json"
        config_json = self.get(key)
        if config_json is None:
            raise LookupError(f"Key {key} does not exist in attributes table")
        config = json.loads(config_json)

        # modify config
        config = update_config(config)

        config_json = json.dumps(config)
        self.update(key, config_json)
