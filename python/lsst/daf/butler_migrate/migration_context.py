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

__all__ = ("MigrationContext",)


import alembic
import sqlalchemy

from .butler_attributes import ButlerAttributes


class MigrationContext:
    """Provides access to commonly-needed objects derived from the alembic
    migration context.
    """

    def __init__(self) -> None:
        self.mig_context = (
            alembic.context.get_context()
        )  #: Alembic migration context for the DB being migrated.
        self.schema = (
            self.mig_context.version_table_schema
        )  #: Database schema name for the repository being migrated.
        bind = self.mig_context.bind
        assert bind is not None, "Can't run offline -- need access to database to migrate data."
        self.bind = bind  #: A SQLAlchemy connection for the database being migrated.
        self.dialect = self.bind.dialect.name  #: SQLAlchemy dialect for the database being migrated.
        self.is_sqlite = self.dialect == "sqlite"  #: True if the database being migrated is SQLite.
        self.metadata = sqlalchemy.schema.MetaData(
            schema=self.schema
        )  # SQLAlchemy MetaData object for the DB being migrated.
        self.attributes = ButlerAttributes(self.bind, self.schema)

    def get_table(self, table_name: str) -> sqlalchemy.Table:
        """Create a SQLAlchemy table object for the current database.

        Parameters
        ----------
        table_name : `str`
            Name of the table.

        Returns
        -------
        table : ``sqlalchemy.Table``
            Table object.
        """
        return sqlalchemy.schema.Table(table_name, self.metadata, autoload_with=self.bind, schema=self.schema)
