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

__all__ = [
    "tree_name_argument",
    "class_argument",
    "version_argument",
    "revision_argument",
    "manager_argument",
    "namespace_argument",
    "tables_argument",
    "instrument_argument",
]

from lsst.daf.butler.cli.utils import MWArgumentDecorator

tree_name_argument = MWArgumentDecorator(
    "tree-name",
    help=(
        "TREE_NAME is the revision tree name, usually it is the name "
        "of a registry manager type (e.g. 'datasets')."
    ),
)

class_argument = MWArgumentDecorator(
    "manager-class",
    help=(
        "MANAGER_CLASS is the name of the manager class (or a namespace in case of special trees), "
        "not including module name."
    ),
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
        "if missing then all managers already defined in butler_attributes "
        "are stamped. To stamp initial revision for a manager not in "
        "butler_attributes, provide its name explicitly."
    ),
    required=False,
)

namespace_argument = MWArgumentDecorator(
    "namespace",
    help=(
        "NAMESPACE to add or replace in the stored dimensions configuration. "
        "If namespace is not specified then existing namespace is printed."
    ),
    required=False,
)

tables_argument = MWArgumentDecorator(
    "table",
    help="TABLE specify multiple optional table names to dump, by default all tables are dumped.",
    required=False,
    nargs=-1,
)

instrument_argument = MWArgumentDecorator(
    "instrument",
    help="INSTRUMENT is the name of the instrument to use.",
    required=True,
)
