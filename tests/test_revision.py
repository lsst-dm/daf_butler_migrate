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

from lsst.daf.butler_migrate import revision


class RevisionTestCase(unittest.TestCase):
    """Tests for revision module"""

    def test_rev_id(self) -> None:
        """Test for rev_id method"""
        args = ["ManagerClass", "1.0.0"]
        rev_id = revision.rev_id(*args)
        self.assertEqual(rev_id, "41f090400d3f")


if __name__ == "__main__":
    unittest.main()
