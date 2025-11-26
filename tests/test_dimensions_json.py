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
import gc
import os
import tempfile
import unittest
from typing import TYPE_CHECKING, Any

import sqlalchemy
import yaml

from lsst.daf.butler import Butler, Config
from lsst.daf.butler.direct_butler import DirectButler
from lsst.daf.butler.tests.utils import makeTestTempDir, removeTestTempDir
from lsst.daf.butler_migrate import butler_attributes, database, migrate, script
from lsst.daf.butler_migrate._dimensions_json_utils import historical_dimensions_resource
from lsst.daf.butler_migrate.revision import rev_id

try:
    import testing.postgresql  # type: ignore[import-untyped]
except ImportError:
    testing = None

if TYPE_CHECKING:

    class TestCaseMixin(unittest.TestCase):
        """Base class for mixin test classes that use TestCase methods."""

else:

    class TestCaseMixin:
        """Do-nothing definition of mixin base class for regular execution."""


TESTDIR = os.path.abspath(os.path.dirname(__file__))

_NAMESPACE = "daf_butler"

_MANAGER = "dimensions-config"


def _revision_id(version: int, namespace: str = "daf_butler") -> str:
    """Return alembic revision name."""
    return rev_id(_MANAGER, namespace, str(version))


def _make_universe(version: int) -> Config:
    """Load dimensions universe for specific version."""
    path = historical_dimensions_resource(version)
    with path.open() as input:
        dimensions = yaml.safe_load(input)
    return Config(dimensions)


class DimensionsJsonTestCase(TestCaseMixin):
    """Tests for migrating of dimensions.json stored configuration."""

    def setUp(self) -> None:
        self.root = makeTestTempDir(TESTDIR)
        self.mig_path = migrate.MigrationTrees.migrations_folder()

    def tearDown(self) -> None:
        removeTestTempDir(self.root)

    def _butler_config(self) -> Config | None:
        """Make configuration for creating new Butlers."""
        raise NotImplementedError()

    def make_butler(self, version: int, **kw: Any) -> str:
        """Make a Butler instance with universe of specific version."""
        dimensions = _make_universe(version)
        # Use unique folder for each butler so we can create many butlers
        # in one unit test.
        butler_root = tempfile.mkdtemp(dir=self.root)
        config = self._butler_config()
        Butler.makeRepo(butler_root, config=config, dimensionConfig=dimensions)
        # Need to stamp current versions into alembic.
        script.migrate_stamp(
            repo=butler_root,
            mig_path=self.mig_path,
            purge=False,
            dry_run=False,
            namespace=_NAMESPACE if version == 0 else None,
            manager=None,
        )
        return butler_root

    def _upgrade_one(self, start_version: int) -> None:
        """Test version upgrade from N to N+1."""
        butler_root = self.make_butler(start_version)
        db = database.Database.from_repo(butler_root)
        self.enterContext(db)

        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, str(start_version), _revision_id(start_version)))

        # Extra version-specific options are needed/
        namespace = None
        options = None
        if start_version == 0:
            namespace = _NAMESPACE
        elif start_version == 1:
            options = {"has_simulated": "0"}

        script.migrate_upgrade(
            repo=butler_root,
            revision=_revision_id(start_version + 1),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=namespace,
            options=options,
        )

        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(
            versions[_MANAGER], (_NAMESPACE, str(start_version + 1), _revision_id(start_version + 1))
        )

    def _downgrade_one(self, start_version: int) -> None:
        """Test version downgrade from N to N-1."""
        butler_root = self.make_butler(start_version)
        db = database.Database.from_repo(butler_root)
        self.enterContext(db)

        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, str(start_version), _revision_id(start_version)))

        script.migrate_downgrade(
            repo=butler_root,
            revision=_revision_id(start_version - 1),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=None,
        )

        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(
            versions[_MANAGER], (_NAMESPACE, str(start_version - 1), _revision_id(start_version - 1))
        )

    def test_upgrade_empty(self) -> None:
        """Simple test for incremental upgrades for all known versions. This
        only tests schema changes with empty registry. More specific test can
        load data to verify that data migration also works OK.
        """
        for start_version in range(6):
            with self.subTest(version=start_version):
                self._upgrade_one(start_version)

    def test_downgrade_empty(self) -> None:
        """Simple test for downgrades for all known versions. This only tests
        schema changes with empty registry.
        """
        for start_version in range(6):
            with self.subTest(version=start_version):
                with contextlib.suppress(NotImplementedError):
                    self._downgrade_one(start_version + 1)

    def test_upgrade_v1(self) -> None:
        """Test for upgrade/downgrade between v0 and v1.

        No actual schema change in this migration, only check that contents of
        ``dimensions.json`` is updated.
        """
        butler_root = self.make_butler(0)
        db = database.Database.from_repo(butler_root)
        self.enterContext(db)

        self.assertIsNone(db.dimensions_namespace())
        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "0", _revision_id(0)))

        # Upgrade to v1.
        script.migrate_upgrade(
            repo=butler_root,
            revision=_revision_id(1),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
            options=None,
        )
        self.assertEqual(db.dimensions_namespace(), _NAMESPACE)
        versions = db.manager_versions()
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "1", _revision_id(1)))

        # Downgrade back to v0.
        script.migrate_downgrade(
            repo=butler_root,
            revision=_revision_id(0),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
        )
        self.assertIsNone(db.dimensions_namespace())
        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "0", _revision_id(0)))

    def test_upgrade_v2(self) -> None:
        """Test for upgrade from v0 to v2.

        Loads some dimension records and verifies that data is migrated
        correctly.
        """
        butler_root = self.make_butler(0)
        db = database.Database.from_repo(butler_root)
        self.enterContext(db)

        self.assertIsNone(db.dimensions_namespace())
        versions = db.manager_versions(_NAMESPACE)
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "0", _revision_id(0)))

        with Butler.from_config(butler_root, writeable=True) as butler:
            assert isinstance(butler, DirectButler), "Only DirectButler is supported"
            butler.import_(filename=os.path.join(TESTDIR, "data", "records.yaml"), without_datastore=True)

            # Check records for v0 attributes.
            records = list(butler.registry.queryDimensionRecords("visit"))
            for record in records:
                self.assertEqual(record.visit_system, 0)

            records = list(butler.registry.queryDimensionRecords("visit_definition"))
            for record in records:
                self.assertEqual(record.visit_system, 0)

        # Upgrade to v1. We could upgrade to v2 in one step but I want to check
        # different arguments at each step.
        script.migrate_upgrade(
            repo=butler_root,
            revision=_revision_id(1),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
            options=None,
        )
        self.assertEqual(db.dimensions_namespace(), _NAMESPACE)
        versions = db.manager_versions()
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "1", _revision_id(1)))

        # Upgrade to v2.
        script.migrate_upgrade(
            repo=butler_root,
            revision=_revision_id(2),
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=None,
            options={"has_simulated": "0"},
        )
        self.assertEqual(db.dimensions_namespace(), _NAMESPACE)
        versions = db.manager_versions()
        self.assertEqual(versions[_MANAGER], (_NAMESPACE, "2", _revision_id(2)))

        butler = Butler.from_config(butler_root, writeable=False)
        self.enterContext(butler)

        # Check records for v2 attributes.
        records = list(butler.registry.queryDimensionRecords("instrument"))
        for record in records:
            self.assertEqual(record.visit_system, 0)

        records = list(butler.registry.queryDimensionRecords("visit"))
        for record in records:
            self.assertFalse(hasattr(record, "visit_system"))
            self.assertIsNone(record.azimuth)
        self.assertEqual({record.id: record.seq_num for record in records}, {1: 100, 2: 200})

        records = list(butler.registry.queryDimensionRecords("exposure"))
        for record in records:
            self.assertFalse(record.has_simulated)
            self.assertIsNone(record.azimuth)
            self.assertEqual(record.seq_start, record.seq_num)
            self.assertEqual(record.seq_end, record.seq_num)

        records = list(butler.registry.queryDimensionRecords("visit_definition"))
        for record in records:
            self.assertFalse(hasattr(record, "visit_system"))

        records = list(butler.registry.queryDimensionRecords("visit_system_membership"))
        self.assertCountEqual(
            [record.toDict() for record in records],
            [
                {"instrument": "Cam", "visit_system": 0, "visit": 1},
                {"instrument": "Cam", "visit_system": 0, "visit": 2},
            ],
        )

    def test_validate_dimensions_json(self) -> None:
        butler_root = self.make_butler(0)
        db = database.Database.from_repo(butler_root)
        self.enterContext(db)
        universe = 5
        with db.connect() as connection:
            attribs = butler_attributes.ButlerAttributes(connection, schema=db.schema)
            with self.assertRaisesRegex(
                ValueError, "dimensions.json stored in database does not match expected"
            ):
                attribs.validate_dimensions_json(universe)

            attribs.replace_dimensions_json(universe)
            attribs.validate_dimensions_json(universe)

    def test_ignore_expected_dimension_json_mismatch(self) -> None:
        original = '{"a": 1, "b": {"doc": "good"}}'
        self.assertTrue(butler_attributes._is_expected_dimensions_json_mismatch(original, original))
        # Mismatched doc but everything else OK
        self.assertTrue(
            butler_attributes._is_expected_dimensions_json_mismatch(original, '{"a": 1, "b": {"doc": "bad"}}')
        )
        # Order doesn't matter
        self.assertTrue(
            butler_attributes._is_expected_dimensions_json_mismatch(original, '{"b": {"doc": "bad"}, "a": 1}')
        )
        # Mismatched non-doc value
        self.assertFalse(
            butler_attributes._is_expected_dimensions_json_mismatch(
                original, '{"a": 2, "b": {"doc": "good"}}'
            )
        )
        # Mismatched value and doc
        self.assertFalse(
            butler_attributes._is_expected_dimensions_json_mismatch(original, '{"a": 2, "b": {"doc": "bad"}}')
        )


class SQLiteDimensionsJsonTestCase(DimensionsJsonTestCase, unittest.TestCase):
    """Test using SQLite backend."""

    def _butler_config(self) -> Config | None:
        return None


@unittest.skipUnless(testing is not None, "testing.postgresql module not found")
class PostgresDimensionsJsonTestCase(DimensionsJsonTestCase, unittest.TestCase):
    """Test using Postgres backend."""

    postgresql: Any

    @classmethod
    def _handler(cls, postgresql: Any) -> None:
        engine = sqlalchemy.engine.create_engine(postgresql.url())
        with engine.begin() as connection:
            connection.execute(sqlalchemy.text("CREATE EXTENSION btree_gist;"))

    @classmethod
    def setUpClass(cls) -> None:
        # Create the postgres test server.
        cls.postgresql = testing.postgresql.PostgresqlFactory(
            cache_initialized_db=True, on_initialized=cls._handler
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        # Clean up any lingering SQLAlchemy engines/connections
        # so they're closed before we shut down the server.
        gc.collect()
        cls.postgresql.clear_cache()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.server = self.postgresql()
        self.count = 0

    def _butler_config(self) -> Config | None:
        # Use unique namespace for each instance, some tests may use sub-tests.
        self.count += 1
        reg_config = {
            "db": self.server.url(),
            "namespace": f"namespace{self.count}",
        }
        return Config({"registry": reg_config})


if __name__ == "__main__":
    unittest.main()
