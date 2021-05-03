# This file is part of daf_butler_smig.
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

from lsst.daf.butler.cli.opt import repo_argument
from lsst.daf.butler.cli.utils import ButlerCommand
from ... import script
from ..opt import (
    class_argument,
    dry_run_option,
    mig_path_option,
    mig_path_exist_option,
    one_shot_option,
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
@click.option("-m", "--manager", help="Manager name, default is to use tree name, but required for one-shot trees.")
@tree_name_argument()
def smig_add_tree(*args, **kwargs):
    """Create new version tree.
    """
    script.smig_add_tree(*args, **kwargs)


@click.command(short_help="Show version history.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
@tree_name_argument(required=False)
def smig_history(*args, **kwargs):
    """Display version history for a tree.
    """
    script.smig_history(*args, **kwargs)


@click.command(short_help="Create migration script for a new revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@tree_name_argument()
@class_argument()
@version_argument()
def smig_revision(*args, **kwargs):
    """Create new revision.
    """
    script.smig_revision(*args, **kwargs)


@click.command(short_help="Print a list of known version trees.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
def smig_trees(*args, **kwargs):
    """Print a list of known version trees.
    """
    script.smig_trees(*args, **kwargs)


@click.command(short_help="Stamp revision table with current registry versions.", cls=ButlerCommand)
@mig_path_exist_option
@purge_option
@dry_run_option
@repo_argument(required=True)
def smig_stamp(*args, **kwargs):
    """Stamp revision table with current registry versions.
    """
    script.smig_stamp(*args, **kwargs)


@click.command(short_help="Display current revisions for a database.", cls=ButlerCommand)
@verbose_option
@click.option("--butler", help="Display butler version numbers for managers.", is_flag=True)
@mig_path_exist_option
@repo_argument(required=True)
def smig_current(*args, **kwargs):
    """Display current revisions for a database.
    """
    script.smig_current(*args, **kwargs)


@click.command(short_help="Upgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@sql_option
@repo_argument(required=True)
@revision_argument(required=True)
def smig_upgrade(*args, **kwargs):
    """Upgrade schema to a specified revision.
    """
    script.smig_upgrade(*args, **kwargs)


@click.command(short_help="Downgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@sql_option
@repo_argument(required=True)
@revision_argument(required=True)
def smig_downgrade(*args, **kwargs):
    """Downgrade schema to a specified revision.
    """
    script.smig_downgrade(*args, **kwargs)
