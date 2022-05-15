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

import click

from ... import migrate

mig_path_option = click.option(
    "--mig-path",
    type=click.Path(exists=False, file_okay=False, writable=True),
    help="Top-level folder with migration scripts, default: " + migrate.MigrationTrees.migrations_folder(),
    metavar="PATH",
    default=migrate.MigrationTrees.migrations_folder(),
)

mig_path_exist_option = click.option(
    "--mig-path",
    type=click.Path(exists=True, file_okay=False, writable=True),
    help="Top-level folder with migration scripts, default: " + migrate.MigrationTrees.migrations_folder(),
    metavar="PATH",
    default=migrate.MigrationTrees.migrations_folder(),
)

one_shot_option = click.option("--one-shot", help="Use special one-shot history trees.", is_flag=True)

one_shot_tree_option = click.option(
    "--one-shot-tree", help="Use special one-shot history tree instead of regular history."
)

verbose_option = click.option("-v", "--verbose", help="Print detailed information.", is_flag=True)

dry_run_option = click.option("-n", "--dry-run", help="Do not execute actions, only report.", is_flag=True)

purge_option = click.option(
    "--purge", help="Remove existing version table before saving new versions.", is_flag=True
)

sql_option = click.option(
    "--sql", help="Offline mode, dump SQL instead of executing migration on a database.", is_flag=True
)

namespace_option = click.option(
    "--namespace",
    help="Namespace to use when 'namespace' key is not present in the stored dimensions configuration",
    default=None,
)
