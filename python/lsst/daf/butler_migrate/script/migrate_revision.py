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

import logging
from typing import Optional

from alembic import command, util
from alembic.script import ScriptDirectory

from .. import config, migrate


_LOG = logging.getLogger(__name__)


def _revision_exists(scripts: ScriptDirectory, revision: str) -> bool:
    """Check that revision exists.
    """
    try:
        scripts.get_revisions(revision)
        return True
    except util.CommandError:
        return False


def migrate_revision(mig_path: str, tree_name: str, manager_class: str,
                     version: str, one_shot: bool) -> None:
    """Create new revision.

    Parameters
    ----------
    mig_path : `str`
        Filesystem path to laocation of revisions.
    tree_name : `str`
        Name of the revision tree.
    manager_class : `str`
        Name of the manager class.
    version : `str`
        Version string, usually in X.Y.Z format.
    one_shot : `bool`
        If `True` make a special one-shot migration.

    Raises
    ------
    LookupError
        Raised if given revision tree name does not exist.
    """
    # class name should not include module name
    if "." in manager_class:
        raise ValueError(f"Manager class name {manager_class!r} must not include module name.")

    if one_shot:
        # One-shot migrations use special logic
        _migrate_revision_one_shot(mig_path, tree_name, manager_class, version)
        return

    # We want to keep trees in separate directories
    migrate_trees = migrate.MigrationTrees(mig_path)
    tree_folder = migrate_trees.regular_version_location(tree_name, relative=False)

    cfg = config.MigAlembicConfig.from_mig_path(mig_path)
    scripts = ScriptDirectory.from_config(cfg)

    # make sure that tree root is defined
    root = migrate.rev_id(tree_name)
    if not _revision_exists(scripts, root):
        raise LookupError(f"Revision tree {tree_name!r} does not exist.")

    # New revision should be either at the head of manager branch or at the
    # root of the tree (to make a new manager branch).
    manager_branch = f"{tree_name}-{manager_class}"
    branch_label: Optional[str] = None
    splice = False
    if _revision_exists(scripts, manager_branch):
        head = f"{manager_branch}@head"
    else:
        # make new branch
        head = root
        branch_label = manager_branch
        splice = True

    # now can make actual revision
    rev_id = migrate.rev_id(tree_name, manager_class, version)
    message = (
        f"Migration script for {manager_class} {version}."
    )
    command.revision(cfg, head=head, rev_id=rev_id, branch_label=branch_label,
                     splice=splice, version_path=tree_folder, message=message)


def _migrate_revision_one_shot(mig_path: str, tree_name: str, manager_class: str,
                               version: str) -> None:

    cfg = config.MigAlembicConfig.from_mig_path(mig_path, single_tree=tree_name)
    scripts = ScriptDirectory.from_config(cfg)

    # We want to keep trees in separate directories
    migrate_trees = migrate.MigrationTrees(mig_path)
    tree_folder = migrate_trees.one_shot_version_location(tree_name, relative=False)

    # we need a manager name, this is a label of a tree root
    bases = scripts.get_bases()
    if not bases:
        raise LookupError(f"Revision tree {tree_name!r} does not exist.")

    # there could be only a single tree
    assert len(bases) == 1

    # Base revision has a random ID but its branch label is "<tree>"
    branches = scripts.get_revision(bases[0]).branch_labels
    assert len(branches) == 1
    manager = branches.pop()

    rev_id = migrate.rev_id(manager, manager_class, version)
    message = (
        f"Migration script for {manager_class} {version}."
    )
    command.revision(cfg, head=f"{manager}@head", rev_id=rev_id, version_path=tree_folder, message=message)
