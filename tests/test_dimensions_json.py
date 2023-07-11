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

import os
import unittest

from lsst.daf.butler import Butler, Config, Registry
from lsst.daf.butler.tests.utils import makeTestTempDir, removeTestTempDir
from lsst.daf.butler.transfers import YamlRepoImportBackend
from lsst.daf.butler_migrate import database, migrate, script

TESTDIR = os.path.abspath(os.path.dirname(__file__))

_NAMESPACE = "daf_butler"

# alembic revisions
_REVISION_V0 = "f3bcee34f344"
_REVISION_V1 = "380002bcbb26"
_REVISION_V2 = "bf6308af80aa"


class DimensionsJsonTestCase(unittest.TestCase):
    """Tests for migrating of dimensions.json stored configuration."""

    def setUp(self) -> None:
        self.root = makeTestTempDir(TESTDIR)
        self.mig_path = migrate.MigrationTrees.migrations_folder()

    def tearDown(self) -> None:
        removeTestTempDir(self.root)

    def make_butler_v0(self) -> Config:
        """Make new Butler instance with dimensions config v0."""
        dimensions = os.path.join(TESTDIR, "config", "dimensions-v0.yaml")
        config = Butler.makeRepo(self.root, dimensionConfig=dimensions)
        # Need to stamp current versions into alembic.
        script.migrate_stamp(
            repo=self.root,
            mig_path=self.mig_path,
            purge=False,
            dry_run=False,
            namespace=_NAMESPACE,
            manager=None,
        )
        self.db = database.Database.from_repo(self.root)
        return config

    def load_data(self, registry: Registry, filename: str) -> None:
        """Load registry test data from filename in data folder."""
        with open(os.path.join(TESTDIR, "data", filename)) as stream:
            backend = YamlRepoImportBackend(stream, registry)
        backend.register()
        backend.load(datastore=None)

    def test_upgrade_v1(self) -> None:
        """Test for upgrade/downgrade between v0 and v1.

        No actual schema change in this migration, only check that contents of
        ``dimensions.json`` is updated.
        """
        self.make_butler_v0()

        self.assertIsNone(self.db.dimensions_namespace())
        versions = self.db.manager_versions(_NAMESPACE)
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "0", _REVISION_V0))

        # Upgrade to v1.
        script.migrate_upgrade(
            repo=self.root,
            revision=_REVISION_V1,
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
            options=None,
        )
        self.assertEqual(self.db.dimensions_namespace(), _NAMESPACE)
        versions = self.db.manager_versions()
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "1", _REVISION_V1))

        # Downgrade back to v0.
        script.migrate_downgrade(
            repo=self.root,
            revision=_REVISION_V0,
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
        )
        self.assertIsNone(self.db.dimensions_namespace())
        versions = self.db.manager_versions(_NAMESPACE)
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "0", _REVISION_V0))

    def test_upgrade_v2(self) -> None:
        """Test for upgrade from v0 to v2.

        Loads some dimension records and verifies that data is migrated
        correctly.
        """
        config = self.make_butler_v0()

        self.assertIsNone(self.db.dimensions_namespace())
        versions = self.db.manager_versions(_NAMESPACE)
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "0", _REVISION_V0))

        butler = Butler(config, writeable=True)
        self.load_data(butler.registry, "records.yaml")

        # Check records for v0 attributes.
        records = list(butler.registry.queryDimensionRecords("visit"))
        for record in records:
            self.assertEqual(record.visit_system, 0)

        records = list(butler.registry.queryDimensionRecords("visit_definition"))
        for record in records:
            self.assertEqual(record.visit_system, 0)

        del butler

        # Upgrade to v1. We could upgrade to v2 in one step but I want to check
        # different arguments at each step.
        script.migrate_upgrade(
            repo=self.root,
            revision=_REVISION_V1,
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=_NAMESPACE,
            options=None,
        )
        self.assertEqual(self.db.dimensions_namespace(), _NAMESPACE)
        versions = self.db.manager_versions()
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "1", _REVISION_V1))

        # Upgrade to v2.
        script.migrate_upgrade(
            repo=self.root,
            revision=_REVISION_V2,
            mig_path=self.mig_path,
            one_shot_tree="",
            sql=False,
            namespace=None,
            options={"has_simulated": "0"},
        )
        self.assertEqual(self.db.dimensions_namespace(), _NAMESPACE)
        versions = self.db.manager_versions()
        self.assertEqual(versions["dimensions-config"], (_NAMESPACE, "2", _REVISION_V2))

        butler = Butler(config, writeable=False)

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


if __name__ == "__main__":
    unittest.main()
