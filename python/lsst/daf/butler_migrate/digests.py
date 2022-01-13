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

__all__ = ["get_digest"]


import hashlib
from typing import Iterable, Set

import sqlalchemy


def get_digest(
    tables: Iterable[sqlalchemy.schema.Table],
    dialect: sqlalchemy.engine.Dialect,
    *,
    nullable_columns: Set[str] = set(),
) -> str:
    """Calculate digest for a schema based on list of tables schemas.

    Parameters
    ----------
    tables : iterable [`sqlalchemy.schema.Table`]
        Set of tables comprising the schema.
    dialect : `sqlalchemy.engine.Dialect`, optional
        Dialect used to stringify types; needed to support dialect-specific
        types.
    nullable_columns: `set` of `str`
        Names of columns which are forced to be nullable. This is used to
        reproduce a case when some PK columns are defined as nullable in
        daf_butler.

    Returns
    -------
    digest : `str`
        String representation of the digest of the schema.

    Notes
    -----
    This is an almost verbatim copy of the code from daf_butler, it is supposed
    to be stable but eventually we need to replace this copy with a call to
    daf_butler method. Digest calculation probably needs an improvement, we
    need to revisit this at some point.
    """
    md5 = hashlib.md5()
    tableSchemas = sorted(_tableSchemaRepr(table, dialect, nullable_columns) for table in tables)
    for tableRepr in tableSchemas:
        md5.update(tableRepr.encode())
    digest = md5.hexdigest()
    return digest


def _tableSchemaRepr(
    table: sqlalchemy.schema.Table, dialect: sqlalchemy.engine.Dialect, nullable_columns: Set[str]
) -> str:
    """Make string representation of a single table schema.

    Parameters
    ----------
    table : `sqlalchemy.schema.Table`
        Tables instance.
    dialect : `sqlalchemy.engine.Dialect`, optional
        Dialect used to stringify types; needed to support dialect-specific
        types.
    nullable_columns: `set` of `str`
        Names of columns which are forced to be nullable. This is used to
        reproduce a case when some PK columns are defined as nullable in
        daf_butler.
    """
    tableSchemaRepr = [table.name]
    schemaReps = []
    for column in table.columns:
        columnRep = f"COL,{column.name},{column.type.compile(dialect=dialect)}"
        if column.primary_key:
            columnRep += ",PK"
        # Unlike corresponding daf_butler method the test also includes
        # explicit list of nullable columns. This is needed to match the
        # behavior of daf_butler method.
        if column.nullable or column.name in nullable_columns:
            columnRep += ",NULL"
        schemaReps += [columnRep]
    for fkConstr in table.foreign_key_constraints:
        # for foreign key we include only one side of relations into
        # digest, other side could be managed by different extension
        fkReps = ["FK", fkConstr.name] + [fk.column.name for fk in fkConstr.elements]
        fkRep = ",".join(fkReps)
        schemaReps += [fkRep]
    # sort everything to keep it stable
    schemaReps.sort()
    tableSchemaRepr += schemaReps
    return ";".join(tableSchemaRepr)
