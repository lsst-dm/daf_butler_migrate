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

from lsst.daf.butler.cli.utils import MWArgumentDecorator

tree_name_argument = MWArgumentDecorator(
    "tree-name",
    help=(
        "TREE_NAME is the revision tree name, usually it is the name "
        "of a registry manager (e.g. 'datasets')."
    ),
)

class_argument = MWArgumentDecorator(
    "manager-class", help="MANAGER_CLASS is the name of the manager class, not including module name."
)

version_argument = MWArgumentDecorator(
    "version", help="VERSION is the version of manager class, typically in X.Y.Z notation."
)

revision_argument = MWArgumentDecorator(
    "revision",
    help=(
        "REVISION is a target alembic revision, in offline mode it can also "
        "specify initial revision using INITIAL:TARGET format."
    ),
)

manager_argument = MWArgumentDecorator(
    "manager",
    help=(
        "MANAGER is a name of the manager for which to stamp the revision, "
        "if missing then all managers are stamped."
    ),
    required=False,
)
