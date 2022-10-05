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

import unittest

import sqlalchemy
from lsst.daf.butler_migrate import digests


class DigestsTestCase(unittest.TestCase):
    """Tests for digests module"""

    def test_tableSchemaRepr(self) -> None:
        """Test for _tableSchemaRepr method"""

        engine = sqlalchemy.create_engine("sqlite://")

        mdata = sqlalchemy.schema.MetaData()
        table1 = sqlalchemy.schema.Table(
            "Table1",
            mdata,
            sqlalchemy.schema.Column("ColumnA", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.schema.Column("ColumnB", sqlalchemy.String(32)),
        )
        table2 = sqlalchemy.schema.Table(
            "Table2",
            mdata,
            sqlalchemy.schema.Column("ColumnX", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.schema.Column("ColumnY", sqlalchemy.Integer, nullable=True),
            sqlalchemy.schema.ForeignKeyConstraint(["ColumnY"], ["Table1.ColumnA"], name="Table2_FK"),
        )
        table_repr = digests._tableSchemaRepr(table1, engine.dialect, set())
        self.assertEqual(table_repr, "Table1;COL,ColumnA,INTEGER,PK;COL,ColumnB,VARCHAR(32),NULL")
        table_repr = digests._tableSchemaRepr(table2, engine.dialect, set())
        self.assertEqual(
            table_repr, "Table2;COL,ColumnX,INTEGER,PK;COL,ColumnY,INTEGER,NULL;FK,Table2_FK,ColumnA"
        )

    def test_tableSchemaRepr_nullpk(self) -> None:
        """Test for _tableSchemaRepr method in case when PK is declared
        nullable.
        """

        engine = sqlalchemy.create_engine("sqlite://")

        # sqlalchemy allows nullable PK columns in table definition
        mdata = sqlalchemy.schema.MetaData()
        table = sqlalchemy.schema.Table(
            "Table1",
            mdata,
            sqlalchemy.schema.Column("ColumnA", sqlalchemy.Integer, primary_key=True, nullable=True),
            sqlalchemy.schema.Column("ColumnB", sqlalchemy.String(32)),
        )
        table_repr1 = digests._tableSchemaRepr(table, engine.dialect, set())
        self.assertEqual(table_repr1, "Table1;COL,ColumnA,INTEGER,PK,NULL;COL,ColumnB,VARCHAR(32),NULL")

        # when the same table schema is reflected from database column is not
        # nullable, to match definition we need to use `nullable_columns`
        mdata = sqlalchemy.schema.MetaData()
        table = sqlalchemy.schema.Table(
            "Table1",
            mdata,
            sqlalchemy.schema.Column("ColumnA", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.schema.Column("ColumnB", sqlalchemy.String(32)),
        )
        table_repr2 = digests._tableSchemaRepr(table, engine.dialect, {"ColumnA"})
        self.assertEqual(table_repr2, table_repr1)


if __name__ == "__main__":
    unittest.main()
