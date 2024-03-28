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

import alembic
import sqlalchemy as sa

from .butler_attributes import ButlerAttributes

__all__ = ("MigrationContext",)


class MigrationContext:
    """Provides access to commonly-needed objects derived from the alembic
    migration context.
    """

    def __init__(self) -> None:
        self.mig_context = alembic.context.get_context()
        self.schema = self.mig_context.version_table_schema
        bind = self.mig_context.bind
        assert bind is not None, "Can't run offline -- need access to database to migrate data."
        self.bind = bind
        self.dialect = self.bind.dialect.name
        self.is_sqlite = self.dialect == "sqlite"
        self.metadata = sa.schema.MetaData(schema=self.schema)
        self.attributes = ButlerAttributes(self.bind, self.schema)

    def get_table(self, table_name: str) -> sa.Table:
        return sa.schema.Table(table_name, self.metadata, autoload_with=self.bind, schema=self.schema)
