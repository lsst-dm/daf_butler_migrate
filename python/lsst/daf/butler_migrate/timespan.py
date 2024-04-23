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

from typing import Any

import sqlalchemy as sa
from lsst.daf.butler import Timespan
from sqlalchemy.dialects.postgresql import INT8RANGE, Range


def create_timespan_column_definitions(column_name: str, dialect: str) -> list[sa.Column]:
    """Generate timespan column definitions for a given SQL dialect.

    Parameters
    ----------
    column_name : `str`
        The name of the column to generate, or the prefix if multiple columns
        are generated.
    dialect : `str`
        The SQL dialect we are generating columns for (``sqlite`` or
        ``postgres``).

    Returns
    -------
    columns : `list` [ `sqlalchemy.Column` ]
        SQLAlchemy column definitions.
    """
    if dialect == "postgresql":
        # Postgres uses a non-standard range datatype for representing
        # timespans.
        return [sa.Column(column_name, INT8RANGE)]
    elif dialect == "sqlite":
        return [
            sa.Column(f"{column_name}_begin", sa.BigInteger),
            sa.Column(f"{column_name}_end", sa.BigInteger),
        ]
    else:
        raise ValueError(f"Unhandled SQL dialect {dialect}")


def format_timespan_value(timespan: Timespan, column_name: str, dialect: str) -> dict[str, Any]:
    """Format timespan values for insertion into a table using SQLAlchemy.

    Parameters
    ----------
    timespan : `Timespan`
        Value being formatted.
    column_name : `str`
        The name of the timespan column, or their prefix if the dialect uses
        multiple columns.
    dialect : `str`
        The SQL dialect we are generating values for (``sqlite`` or
        ``postgres``).

    Returns
    -------
    values : `dict` [ `str`, `typing.Any` ]
        Mapping from column name to value for that column.
    """
    nanoseconds = timespan.nsec
    if dialect == "postgresql":
        return {column_name: Range(*nanoseconds)}
    elif dialect == "sqlite":
        return {
            f"{column_name}_begin": nanoseconds[0],
            f"{column_name}_end": nanoseconds[1],
        }
    else:
        raise ValueError(f"Unhandled SQL dialect {dialect}")
