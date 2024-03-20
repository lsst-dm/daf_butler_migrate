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

__all__ = [
    "foreign_key_index_name",
    "foreign_key_name",
    "index_name",
    "primary_key_name",
    "sequence_name",
    "unique_key_name",
]

from typing import TYPE_CHECKING

import sqlalchemy

from .shrink import shrinkDatabaseEntityName

if TYPE_CHECKING:
    from collections.abc import Iterable


def primary_key_name(table: str, bind: sqlalchemy.engine.Connection) -> str:
    """Return name of a primary key constraint for a table.

    Parameters
    ----------
    table : `str`
        Table name, not including schema name.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = f"{table}_pkey"
    return shrinkDatabaseEntityName(entity_name, bind)


def unique_key_name(table: str, columns: Iterable[str], bind: sqlalchemy.engine.Connection) -> str:
    """Return name of a unique constraint for a table.

    Parameters
    ----------
    table : `str`
        Table name, not including schema name.
    columns : `~collections.abc.Iterable` [`str`]
        Names of columns in the constraint.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = "_".join([table, "unq"] + list(columns))
    return shrinkDatabaseEntityName(entity_name, bind)


def foreign_key_name(
    table: str,
    columns: Iterable[str],
    parent_table: str,
    parent_columns: Iterable[str],
    bind: sqlalchemy.engine.Connection,
) -> str:
    """Return name of a foreign key constraint for a table.

    Parameters
    ----------
    table : `str`
        Referring table name, not including schema name.
    columns : `~collections.abc.Iterable` [`str`]
        Names of columns in the referring table.
    parent_table : `str`
        Parent (referred) table name, not including schema name.
    parent_columns : `~collections.abc.Iterable` [`str`]
        Names of columns in the referred table.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = "_".join(["fkey", table, parent_table] + list(parent_columns) + list(columns))
    return shrinkDatabaseEntityName(entity_name, bind)


def sequence_name(table: str, column: str, bind: sqlalchemy.engine.Connection) -> str:
    """Return name of a sequence used to populate an auto-increment column.

    Parameters
    ----------
    table : `str`
        Table name, not including schema name.
    column : `str`
        Column name.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = f"{table}_seq_{column}"
    return shrinkDatabaseEntityName(entity_name, bind)


def index_name(table: str, columns: Iterable[str], bind: sqlalchemy.engine.Connection) -> str:
    """Return name of a regular (non-FK) index.

    Parameters
    ----------
    table : `str`
        Table name, not including schema name.
    columns : `~collections.abc.Iterable` [`str`]
        Names of columns in the index.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = "_".join([table, "idx"] + list(columns))
    return shrinkDatabaseEntityName(entity_name, bind)


def foreign_key_index_name(table: str, columns: Iterable[str], bind: sqlalchemy.engine.Connection) -> str:
    """Return name of an index on foreign key columns.

    Parameters
    ----------
    table : `str`
        Table name, not including schema name.
    columns : `~collections.abc.Iterable` [`str`]
        Names of columns in the index.
    bind : `sqlalchemy.engine.Connection`
        Database connection.

    Notes
    -----
    This reproduces naming as defined in
    `lsst.daf.butler.registry.interfaces.Database`.
    """
    entity_name = "_".join([table, "fkidx"] + list(columns))
    return shrinkDatabaseEntityName(entity_name, bind)


def is_foreign_key_index(table: str, index_name: str) -> bool:
    return index_name.startswith(f"{table}_fkidx_")


def is_regular_index(table: str, index_name: str) -> bool:
    return index_name.startswith(f"{table}_idx_")


def make_string_length_constraint(
    column_name: str, max_length: int, constraint_name: str
) -> sqlalchemy.schema.CheckConstraint:
    """Create a check constraint that guarantees a string column has a length
    that is non-zero and less than a specified maximum.

    These constraints are used by Butler in sqlite databases to emulate
    VARCHARs with a specific length.

    Parameters
    ----------
    column_name : `str`
        The name of the column to create the constraint on.
    max_length : `int`
        The maximum length allowed for strings stored in this column.
    constraint_name : `str`
        An arbitrary identifier for the constraint.

    Returns
    -------
    check_constraint : `sqlalchemy.schema.CheckConstraint`
        The generated check constraint.
    """
    return sqlalchemy.schema.CheckConstraint(
        f'length("{column_name}")<={max_length} AND length("{column_name}")>=1', name=constraint_name
    )
