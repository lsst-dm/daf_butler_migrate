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
from collections.abc import Callable, Iterable
from typing import Any, cast

import sqlalchemy

from ._dimensions_json_utils import compare_json_strings, load_historical_dimension_universe_json

_DIMENSIONS_JSON_KEY = "config:dimensions.json"


class ButlerAttributes:
    """Helper class implementing updates for butler_attributes table.

    Parameters
    ----------
    connection : `sqlalchemy.engine.Connection`
        Database connection.
    schema : str, optional
        Schema name or `None`.
    """

    def __init__(self, connection: sqlalchemy.engine.Connection, schema: str | None = None):
        self._connection = connection
        metadata = sqlalchemy.schema.MetaData(schema=schema)
        self._table = sqlalchemy.schema.Table(
            "butler_attributes",
            metadata,
            sqlalchemy.schema.Column("name", sqlalchemy.Text, primary_key=True),
            sqlalchemy.schema.Column("value", sqlalchemy.Text, nullable=False),
            schema=schema,
        )

    def get(self, name: str) -> str | None:
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

    def items(self) -> Iterable[tuple[str, str]]:
        """Retrieve all records from attributes table.

        Returns
        -------
        records : `Iterable`[`tuple`[`str`, `str`]]
            Sequence of tuples, each tuple contains attribute name and its
            value.
        """
        sql = sqlalchemy.sql.select(self._table.columns.name, self._table.columns.value)
        result = self._connection.execute(sql)
        return [cast(tuple[str, str], row) for row in result.fetchall()]

    def insert(self, name: str, value: str) -> None:
        """Insert new parameter in butler_attributes table.

        Parameters
        ----------
        name : `str`
            New attribute name.
        value : `str`
            Attribute value.
        """
        sql = self._table.insert().values(name=name, value=value)
        self._connection.execute(sql)

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
        result = self._connection.execute(sql)
        # result may be None in offline mode, assume that we updated something
        return 1 if result is None else result.rowcount

    def update_manager_version(self, manager: str, version: str) -> None:
        """Update version for the specified manager.

        Parameters
        ----------
        manager : `str`
            Manager name.
        version : `str`
            New version string.

        Raises
        ------
        LookupError
            Raised if manager is not found in the table.
        """
        manager_key = f"version:{manager}"
        count = self.update(manager_key, version)
        if count != 1:
            raise LookupError(f"Manager key {manager_key} is not found in butler_attributes table.")

    def delete(self, name: str) -> int:
        """Delete parameter from butler_attributes table.

        Parameters
        ----------
        name : `str`
            Attribute name.

        Returns
        -------
        count : `int`
            Number of deleted rows, 0 if no matching attribute found, 1
            otherwise.
        """
        sql = self._table.delete().where(self._table.columns.name == name)
        result = self._connection.execute(sql)
        # result may be None in offline mode, assume that we deleted something
        return 1 if result is None else result.rowcount

    def get_dimensions_json(self) -> dict[str, Any]:
        """Return dimensions configuration from dimensions.json.

        Returns
        -------
        config : `dict`
            Contents of ``dimensions.json`` as dictionary.
        """
        config = json.loads(self._load_dimensions_json())
        return config

    def _load_dimensions_json(self) -> str:
        key = _DIMENSIONS_JSON_KEY
        config_json = self.get(key)
        if config_json is None:
            raise LookupError(f"Key {key} does not exist in attributes table")
        return config_json

    def update_dimensions_json(self, update_config: Callable[[dict], dict]) -> None:
        """Update dimensions definitions in dimensions.json.

        Parameters
        ----------
        update_config : `Callable`
            A method that takes a dictionary representation of the
            ``dimensions.json`` and returns an updated dictionary.
        """
        key = _DIMENSIONS_JSON_KEY
        config_json = self.get(key)
        if config_json is None:
            raise LookupError(f"Key {key} does not exist in attributes table")
        config = json.loads(config_json)

        # modify config
        config = update_config(config)

        config_json = json.dumps(config)
        self.update(key, config_json)

    def validate_dimensions_json(self, expected_universe_version: int) -> None:
        """
        Compare the dimensions.json definition stored in the attributes table
        with the default daf_butler dimensions.json at a specific version, and
        raise an exception if they do not match.

        Parameters
        ----------
        expected_universe_version : `int`
            Version number of the daf_butler universe that we expect to find in
            the DB.

        Raises
        ------
        ValueError
            If the dimension universe stored in the database does not match the
            expected value.
        """
        expected_json = load_historical_dimension_universe_json(expected_universe_version)
        actual_json = self._load_dimensions_json()
        diff = compare_json_strings(expected_json, actual_json)
        if diff is not None and not _is_expected_dimensions_json_mismatch(expected_json, actual_json):
            err = ValueError(
                "dimensions.json stored in database does not match expected"
                f" daf_butler universe version {expected_universe_version}."
            )
            err.add_note(f"Differences:\n\n{diff}")
            raise err

        return None

    def replace_dimensions_json(self, universe_version: int) -> None:
        """Replace the dimensions.json definition stored in the attributes
        table to match the default daf_butler dimensions.json at a specific
        version.

        Parameters
        ----------
        universe_version : `int`
            Version number for the daf_butler universe to be saved in the DB.
        """
        dimensions = load_historical_dimension_universe_json(universe_version)
        self.update(_DIMENSIONS_JSON_KEY, dimensions)


def _is_expected_dimensions_json_mismatch(expected_json: str, actual_json: str) -> bool:
    # Return `True` if the two dimension universe JSON strings differ only in
    # ways expected because of the history of this data.  Older repositories
    # that have been previously migrated have some documentation strings that
    # don't match the current dimension universe because of how dimension
    # universes were patched in earlier migrations.

    diff = compare_json_strings(
        _strip_doc_properties_from_json(expected_json), _strip_doc_properties_from_json(actual_json)
    )
    return diff is None


def _strip_doc_properties_from_json(json_string: str) -> str:
    # Remove any properties named 'doc' from objects in the given JSON string.
    dictionary = json.loads(json_string)
    stripped = _strip_doc_properties_from_dict(dictionary)
    return json.dumps(stripped)


def _strip_doc_properties_from_dict(dictionary: dict[str, object]) -> dict[str, object]:
    # Recursively remove any properties named 'doc' from the given dict or any
    # dicts in its values.
    stripped: dict[str, object] = {}
    for key, value in dictionary.items():
        if key != "doc":
            if isinstance(value, dict):
                stripped[key] = _strip_doc_properties_from_dict(value)
            else:
                stripped[key] = value

    return stripped
