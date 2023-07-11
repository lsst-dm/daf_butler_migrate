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
import os
import unittest
from collections.abc import Iterator

from lsst.daf.butler_migrate import migrate
from lsst.utils.tests import temporaryDirectory

# folders to create in migrations directory
_folders = (
    "_alembic",
    "_oneshot/datasets/migration1",
    "_oneshot/datasets/migration2",
    "_oneshot/dimensions/mig1",
    "_oneshot/dimensions/mig2",
    "collections/m1",
    "collections/m2",
    "collections/m3",
    "datasets/m1",
    "datasets/m2",
    "dimensions/m1",
)


@contextlib.contextmanager
def make_migrations() -> Iterator[str]:
    """Generate folder structure for migrations.

    Yields
    ------
    path : `str`
        Path to migration tree folder.
    """
    with temporaryDirectory() as folder:
        for path in _folders:
            os.makedirs(os.path.join(folder, path))
        yield folder


class MigrateTestCase(unittest.TestCase):
    """Tests for migrate module"""

    def test_MigrationTrees(self) -> None:
        """Test for MigrationTrees methods"""
        with make_migrations() as mig_path:
            mtrees = migrate.MigrationTrees(mig_path)

            self.assertEqual(mtrees.mig_path, mig_path)

            self.assertEqual(mtrees.alembic_folder(), "_alembic")
            self.assertEqual(mtrees.alembic_folder(relative=False), os.path.join(mig_path, "_alembic"))

            self.assertEqual(mtrees.regular_version_location("managerA"), "managerA")
            self.assertEqual(
                mtrees.regular_version_location("managerA", relative=False),
                os.path.join(mig_path, "managerA"),
            )

            locations = mtrees.regular_version_locations()
            self.assertEqual(
                locations,
                {
                    "collections": "collections",
                    "datasets": "datasets",
                    "dimensions": "dimensions",
                },
            )
            locations = mtrees.regular_version_locations(relative=False)
            self.assertEqual(
                locations,
                {
                    "collections": os.path.join(mig_path, "collections"),
                    "datasets": os.path.join(mig_path, "datasets"),
                    "dimensions": os.path.join(mig_path, "dimensions"),
                },
            )

            locations = mtrees.one_shot_locations()
            self.assertEqual(
                locations,
                {
                    "datasets/migration1": "_oneshot/datasets/migration1",
                    "datasets/migration2": "_oneshot/datasets/migration2",
                    "dimensions/mig1": "_oneshot/dimensions/mig1",
                    "dimensions/mig2": "_oneshot/dimensions/mig2",
                },
            )

            locations = mtrees.one_shot_locations("datasets")
            self.assertEqual(
                locations,
                {
                    "datasets/migration1": "_oneshot/datasets/migration1",
                    "datasets/migration2": "_oneshot/datasets/migration2",
                },
            )
            locations = mtrees.one_shot_locations("datasets", relative=False)
            self.assertEqual(
                locations,
                {
                    "datasets/migration1": os.path.join(mig_path, "_oneshot/datasets/migration1"),
                    "datasets/migration2": os.path.join(mig_path, "_oneshot/datasets/migration2"),
                },
            )

            locations_list = mtrees.version_locations()
            self.assertCountEqual(locations_list, ["collections", "datasets", "dimensions"])

            locations_list = mtrees.version_locations("datasets/migration1")
            self.assertCountEqual(
                locations_list, ["collections", "_oneshot/datasets/migration1", "dimensions"]
            )

            locations_list = mtrees.version_locations("dimensions/mig2", relative=False)
            self.assertCountEqual(
                locations_list,
                [
                    os.path.join(mig_path, "collections"),
                    os.path.join(mig_path, "datasets"),
                    os.path.join(mig_path, "_oneshot/dimensions/mig2"),
                ],
            )


if __name__ == "__main__":
    unittest.main()
