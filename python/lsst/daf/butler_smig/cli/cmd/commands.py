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

# from lsst.daf.butler.cli.opt import repo_argument
from lsst.daf.butler.cli.utils import ButlerCommand
from ... import script
from ..opt import (
    class_argument,
    mig_path_option,
    mig_path_exist_option,
    one_shot_option,
    tree_name_argument,
    tree_name_argument_optional,
    verbose_option,
    version_argument,
)


@click.command(short_help="Create new version tree.", cls=ButlerCommand)
@mig_path_option
@one_shot_option
@tree_name_argument
def smig_add_tree(*args, **kwargs):
    """Display version history for a tree.
    """
    script.smig_add_tree(*args, **kwargs)


@click.command(short_help="Show version history.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
@tree_name_argument_optional
def smig_history(*args, **kwargs):
    """Display version history for a tree.
    """
    script.smig_history(*args, **kwargs)


@click.command(short_help="Create migration script for a new revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@tree_name_argument
@class_argument
@version_argument
def smig_revision(*args, **kwargs):
    """Create new revision.
    """
    script.smig_revision(*args, **kwargs)


@click.command(short_help="Print a list of known version trees.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
def smig_trees(*args, **kwargs):
    """Display version history for a tree.
    """
    script.smig_trees(*args, **kwargs)
