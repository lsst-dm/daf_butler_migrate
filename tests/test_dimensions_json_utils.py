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

import json
import unittest

from lsst.daf.butler_migrate._dimensions_json_utils import (
    compare_json_strings,
    load_historical_dimension_universe_json,
)


class DimensionUtilsTestCase(unittest.TestCase):
    """Test dimensions JSON utility functions."""

    def test_universe_load(self) -> None:
        self._check_universe_load(5)
        self._check_universe_load(6)

    def _check_universe_load(self, version: int) -> None:
        universe = load_historical_dimension_universe_json(version)
        loaded_version_number = json.loads(universe)["version"]
        self.assertEqual(loaded_version_number, version)

    def test_equal_json_strings(self) -> None:
        a = '{ "a": {"b": 1, "c": 2}}'
        b = '{ "a": {"c": 2,        "b": 1}}'
        self.assertIsNone(compare_json_strings(a, b))

    def test_non_equal_json_strings(self) -> None:
        a = '{ "a": 1 }'
        b = '{ "a": {"c": 2,        "b": 1}}'
        diff = compare_json_strings(a, b)
        self.assertEqual(
            diff,
            """--- \n+++ \n@@ -1,3 +1,6 @@\n {\n-  "a": 1\n+  "a": {\n+    "b": 1,\n+    "c": 2\n+  }\n }""",
        )


if __name__ == "__main__":
    unittest.main()
