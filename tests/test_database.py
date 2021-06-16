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

import contextlib
import unittest

import sqlalchemy

from lsst.daf.butler_migrate import database, revision
from lsst.utils.tests import temporaryDirectory


# queries to create/fill butler_attributes table
_queries = (
    "CREATE TABLE butler_attributes (name TEXT, value TEXT NOT NULL, PRIMARY KEY (name))",
    ("INSERT INTO butler_attributes (name, value) "
     "VALUES ('config:registry.managers.manager1', 'pkg1.module1.Manager1') "),
    ("INSERT INTO butler_attributes (name, value) "
     "VALUES ('config:registry.managers.manager2', 'Manager2') "),
    "INSERT INTO butler_attributes (name, value) VALUES ('version:pkg1.module1.Manager1', '0.0.1') ",
    "INSERT INTO butler_attributes (name, value) VALUES ('version:Manager2', '1.0.0') ",
)


@contextlib.contextmanager
def make_butler_attributes():
    """Create simple sqlite database with butler_attributes populated.

    Yields
    ------
    db_url : `str`
        URL for the database.
    """
    with temporaryDirectory() as folder:
        db_url = f"sqlite:///{folder}/test_db.sqlite3"
        engine = sqlalchemy.create_engine(db_url)
        with engine.connect() as conn:
            for query in _queries:
                conn.execute(sqlalchemy.text(query))
        yield db_url


class DatabaseTestCase(unittest.TestCase):
    """Tests for database module"""

    def test_manager_versions(self):
        """Test for manager_versions() method"""

        with make_butler_attributes() as db_url:
            db = database.Database(db_url)
            manager_versions = db.manager_versions()
            self.assertEqual(manager_versions, {
                "manager1": ("pkg1.module1.Manager1", "0.0.1",
                             revision.rev_id("manager1", "Manager1", "0.0.1")),
                "manager2": ("Manager2", "1.0.0", revision.rev_id("manager2", "Manager2", "1.0.0")),
            })


if __name__ == "__main__":
    unittest.main()
