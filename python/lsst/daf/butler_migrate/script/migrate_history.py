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

"""Dump configuration.
"""

from __future__ import annotations

from alembic import command

from .. import config, migrate


def migrate_history(tree_name: str, mig_path: str, verbose: bool, one_shot: bool) -> None:
    """Print version history for a given tree.

    Parameters
    ----------
    tree_name : `str`
        Name of the revision tree.
    mig_path : `str`
        Filesystem path to laocation of revisions.
    verbose : `bool`
        Print verbose information if this flag is true.
    one_shot : `bool`
        If `True` make a special one-shot migration.
    """
    if one_shot:
        _one_shot_migrate_history(tree_name, mig_path, verbose)
        return None

    # limit to a single location if tree name is given
    if tree_name:
        cfg = config.SmigAlembicConfig.from_mig_path(mig_path, single_tree=tree_name)
    else:
        cfg = config.SmigAlembicConfig.from_mig_path(mig_path)

    command.history(cfg, verbose=verbose)


def _one_shot_migrate_history(tree_name: str, mig_path: str, verbose: bool) -> None:

    if tree_name:
        # if tree name is given then nothing to do for us
        cfg = config.SmigAlembicConfig.from_mig_path(mig_path, single_tree=tree_name)
        command.history(cfg, verbose=verbose)
    else:

        migrate_trees = migrate.MigrationTrees(mig_path)
        locations = migrate_trees.one_shot_locations(relative=False)
        for tree_name in locations.keys():
            cfg = config.SmigAlembicConfig.from_mig_path(mig_path, single_tree=tree_name)
            command.history(cfg, verbose=verbose)
