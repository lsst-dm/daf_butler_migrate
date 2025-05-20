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

from typing import Any, Literal

import alembic
import sqlalchemy

from .butler_attributes import ButlerAttributes


class MigrationContext:
    """Provides access to commonly-needed objects derived from the alembic
    migration context.

    Parameters
    ----------
    manager : `str`, optional
        Full name of manager class, has to be provided if the instance is used
        as context manager.
    version : `str`, optional
        Final version to store in ``butler_attributes`` table, has to be
        provided if the instance is used as context manager.
    """

    def __init__(self, manager: str | None = None, version: str | None = None) -> None:
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
        self._manager = manager
        self._version = version

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

    def __enter__(self) -> MigrationContext:
        """Enter the context, on exit it will store new manager version in
        ``butler_attributes`` table.

        Notes
        -----
        This context manager cannot be used with dimensions-config tree.
        """
        if not (self._manager and self._version):
            raise ValueError("Manager name and version number has to be provided in constructor.")
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> Literal[False]:
        """Store new manager version if no exceptions happened."""
        if exc_type is None:
            assert self._manager is not None and self._version is not None
            self.attributes.update_manager_version(self._manager, self._version)
        return False
