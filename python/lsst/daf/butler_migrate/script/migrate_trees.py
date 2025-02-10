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

"""Dump configuration."""

from __future__ import annotations

from alembic.script import Script, ScriptDirectory

from .. import config, migrate


def migrate_trees(mig_path: str, verbose: bool, one_shot: bool) -> None:
    """Print list of known revision trees.

    Parameters
    ----------
    mig_path : `str`
        Filesystem path to location of revision trees.
    verbose : `bool`
        Print verbose information if this flag is true.
    one_shot : `bool`
        If `True` print locations for special one-shot migrations.
    """
    if one_shot:
        _migrate_trees_one_shot(mig_path, verbose)
        return

    cfg = config.MigAlembicConfig.from_mig_path(mig_path)
    scripts = ScriptDirectory.from_config(cfg)
    bases = scripts.get_bases()

    bases_map: dict[str, Script] = {}
    for name in bases:
        revision = scripts.get_revision(name)
        assert revision is not None, "Script for a known base must exist"
        # Base revision has a random ID but its branch label is "<tree>"
        branches = revision.branch_labels
        if not branches:
            branch = name
        elif len(branches) == 1:
            branch = branches.pop()
        else:
            # Multiple branch labels, usually means that there is one
            # branch and "manager-ClassName" branch label "leaked" to the
            # root. Just use shortest name, that should be sufficient.
            _, branch = min((len(label), label) for label in branches)
        bases_map[branch] = revision

    for branch, revision in sorted(bases_map.items()):
        if verbose:
            print(revision.log_entry)
        else:
            print(branch)


def _migrate_trees_one_shot(mig_path: str, verbose: bool) -> None:
    # one-shot trees are just folders in _oneshot folder

    migrate_trees = migrate.MigrationTrees(mig_path)

    one_shot_locations = migrate_trees.one_shot_locations()
    tree_names = sorted(one_shot_locations.keys())

    for entry in sorted(tree_names):
        cfg = config.MigAlembicConfig.from_mig_path(mig_path, single_tree=entry)
        scripts = ScriptDirectory.from_config(cfg)

        if verbose:
            bases = scripts.get_bases()
            if bases:
                assert len(bases) == 1
                revision = scripts.get_revision(bases[0])
                assert revision is not None, "Script for a known base must exist"
                print(revision.log_entry)
        else:
            print(entry)
