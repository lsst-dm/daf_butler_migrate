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

import click
from typing import Any

from lsst.daf.butler.cli.opt import repo_argument
from lsst.daf.butler.cli.utils import ButlerCommand
from ... import script
from ..opt import (
    class_argument,
    dry_run_option,
    mig_path_option,
    mig_path_exist_option,
    one_shot_option,
    one_shot_tree_option,
    purge_option,
    revision_argument,
    sql_option,
    tree_name_argument,
    verbose_option,
    version_argument,
)


@click.command(short_help="Create new version tree.", cls=ButlerCommand)
@mig_path_option
@one_shot_option
@tree_name_argument()
def migrate_add_tree(*args: Any, **kwargs: Any) -> None:
    """Create new version tree.
    """
    script.migrate_add_tree(*args, **kwargs)


@click.command(short_help="Show version history.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
@tree_name_argument(required=False)
def migrate_history(*args: Any, **kwargs: Any) -> None:
    """Display version history for a tree.
    """
    script.migrate_history(*args, **kwargs)


@click.command(short_help="Create migration script for a new revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@tree_name_argument()
@class_argument()
@version_argument()
def migrate_revision(*args: Any, **kwargs: Any) -> None:
    """Create new revision.
    """
    script.migrate_revision(*args, **kwargs)


@click.command(short_help="Print a list of known version trees.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
def migrate_trees(*args: Any, **kwargs: Any) -> None:
    """Print a list of known version trees.
    """
    script.migrate_trees(*args, **kwargs)


@click.command(short_help="Stamp revision table with current registry versions.", cls=ButlerCommand)
@mig_path_exist_option
@purge_option
@dry_run_option
@repo_argument(required=True)
def migrate_stamp(*args: Any, **kwargs: Any) -> None:
    """Stamp revision table with current registry versions.
    """
    script.migrate_stamp(*args, **kwargs)


@click.command(short_help="Display current revisions for a database.", cls=ButlerCommand)
@verbose_option
@click.option("--butler", help="Display butler version numbers for managers.", is_flag=True)
@mig_path_exist_option
@repo_argument(required=True)
def migrate_current(*args: Any, **kwargs: Any) -> None:
    """Display current revisions for a database.
    """
    script.migrate_current(*args, **kwargs)


@click.command(short_help="Upgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_tree_option
@sql_option
@repo_argument(required=True)
@revision_argument(required=True)
def migrate_upgrade(*args: Any, **kwargs: Any) -> None:
    """Upgrade schema to a specified revision.
    """
    script.migrate_upgrade(*args, **kwargs)


@click.command(short_help="Downgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_tree_option
@sql_option
@repo_argument(required=True)
@revision_argument(required=True)
def migrate_downgrade(*args: Any, **kwargs: Any) -> None:
    """Downgrade schema to a specified revision.
    """
    script.migrate_downgrade(*args, **kwargs)
