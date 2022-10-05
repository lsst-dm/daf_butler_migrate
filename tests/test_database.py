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
from collections.abc import Iterator

import sqlalchemy
from lsst.daf.butler_migrate import database, revision
from lsst.utils.tests import temporaryDirectory

# queries to create/fill tables in test database
_queries_butler_attributes = [
    "CREATE TABLE butler_attributes (name TEXT, value TEXT NOT NULL, PRIMARY KEY (name))",
    (
        "INSERT INTO butler_attributes (name, value) "
        "VALUES ('config:registry.managers.manager1', 'pkg1.module1.Manager1') "
    ),
    (
        "INSERT INTO butler_attributes (name, value) "
        "VALUES ('config:registry.managers.manager2', 'Manager2') "
    ),
    "INSERT INTO butler_attributes (name, value) VALUES ('version:pkg1.module1.Manager1', '0.0.1')",
    "INSERT INTO butler_attributes (name, value) VALUES ('version:Manager2', '1.0.0')",
]

_queries_alembic_version = [
    "CREATE TABLE alembic_version (version_num VARCHAR(32), PRIMARY KEY (version_num))",
    "INSERT INTO alembic_version (version_num) VALUES ('{}')".format(
        revision.rev_id("manager1", "Manager1", "0.0.1")
    ),
    "INSERT INTO alembic_version (version_num) VALUES ('{}')".format(
        revision.rev_id("manager2", "Manager2", "1.0.0")
    ),
]

_broken_alembic_version = [
    "INSERT INTO alembic_version (version_num) VALUES ('nonsense1')",
    "INSERT INTO alembic_version (version_num) VALUES ('nonsense2')",
]


@contextlib.contextmanager
def make_revision_tables(
    make_butler: bool = True,
    fill_butler: bool = True,
    make_alembic: bool = True,
    fill_alembic: bool = True,
    broken_alembic: bool = False,
) -> Iterator[str]:
    """Create simple sqlite database with butler_attributes populated.

    Yields
    ------
    db_url : `str`
        URL for the database.
    """
    # make the list of
    queries = []
    if make_butler:
        queries += _queries_butler_attributes[:1]
        if fill_butler:
            queries += _queries_butler_attributes[1:]
    if make_alembic:
        queries += _queries_alembic_version[:1]
        if fill_alembic:
            if broken_alembic:
                queries += _broken_alembic_version
            else:
                queries += _queries_alembic_version[1:]

    with temporaryDirectory() as folder:
        db_url = f"sqlite:///{folder}/test_db.sqlite3"
        engine = sqlalchemy.create_engine(db_url)
        with engine.connect() as conn:
            for query in queries:
                conn.execute(sqlalchemy.text(query))
        yield db_url


class DatabaseTestCase(unittest.TestCase):
    """Tests for database module"""

    def test_manager_versions(self) -> None:
        """Test for manager_versions() method"""

        with make_revision_tables() as db_url:
            db = database.Database(db_url)
            manager_versions = db.manager_versions()
            self.assertEqual(
                manager_versions,
                {
                    "manager1": (
                        "pkg1.module1.Manager1",
                        "0.0.1",
                        revision.rev_id("manager1", "Manager1", "0.0.1"),
                    ),
                    "manager2": ("Manager2", "1.0.0", revision.rev_id("manager2", "Manager2", "1.0.0")),
                },
            )

    def test_alembic_revisions(self) -> None:
        """Test for alembic_revisions() method"""

        with make_revision_tables() as db_url:
            db = database.Database(db_url)
            alembic_revisions = db.alembic_revisions()
            self.assertCountEqual(
                alembic_revisions,
                [
                    revision.rev_id("manager1", "Manager1", "0.0.1"),
                    revision.rev_id("manager2", "Manager2", "1.0.0"),
                ],
            )

    def test_validate_revisions(self) -> None:
        """Test for validate_revisions() method"""

        with make_revision_tables() as db_url:
            db = database.Database(db_url)
            db.validate_revisions()

        with make_revision_tables(make_alembic=False) as db_url:
            db = database.Database(db_url)
            with self.assertRaisesRegex(
                database.RevisionConsistencyError, "alembic_version table does not exist or is empty"
            ):
                db.validate_revisions()

        with make_revision_tables(fill_alembic=False) as db_url:
            db = database.Database(db_url)
            with self.assertRaisesRegex(
                database.RevisionConsistencyError, "alembic_version table does not exist or is empty"
            ):
                db.validate_revisions()

        with make_revision_tables(make_butler=False) as db_url:
            db = database.Database(db_url)
            with self.assertRaisesRegex(
                database.RevisionConsistencyError, "butler_attributes table does not exist"
            ):
                db.validate_revisions()

        with make_revision_tables(fill_butler=False) as db_url:
            db = database.Database(db_url)
            with self.assertRaisesRegex(
                database.RevisionConsistencyError, "butler_attributes table is empty"
            ):
                db.validate_revisions()

        with make_revision_tables(broken_alembic=True) as db_url:
            db = database.Database(db_url)
            with self.assertRaisesRegex(
                database.RevisionConsistencyError, "Butler and alembic revisions are inconsistent"
            ):
                db.validate_revisions()


if __name__ == "__main__":
    unittest.main()
