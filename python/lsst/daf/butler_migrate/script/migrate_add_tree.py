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
import os

from alembic import command

from .. import config, migrate


_LOG = logging.getLogger(__name__)


def migrate_add_tree(tree_name: str, mig_path: str, one_shot: bool) -> None:
    """Add one more revision tree.

    Parameters
    ----------
    tree_name : `str`
        Name of the revision tree.
    mig_path : `str`
        Filesystem path to location of revisions.
    one_shot : `bool`
        If `True` make tree for a special one-shot migrations.

    Raises
    ------
    ValueError
        Raised if given revision tree name already exists.

    Notes
    -----
    Regular trees are stored in per-manager directories just below the
    top-level migration folder, e.g. "migrations/datasets/". One-shot trees
    are stored inside "_oneshot" folder, one directory per tree, e.g.
    "migrations/_oneshot/datasets-special-xyz/".

    This call generates a root revision for a tree. Revision ID of the root is
    generated based on manager name, which also means that one-shot revisions
    revisions will conflict with regular trees and other one-shot trees. For
    all trees the root of the tree is labelled with the manager name (e.g.
    "datasets").
    """

    trees = migrate.MigrationTrees(mig_path)

    manager = tree_name
    if one_shot:
        manager, _, name = tree_name.partition("/")
        if not name:
            raise ValueError("One-shot tree name requires manager name and slash character: f{tree_name}.")
    else:
        if "/" in tree_name:
            raise ValueError("Regular tree name cannot have slash character: f{tree_name}.")

    # check that its folder does not exist yet
    if one_shot:
        tree_folder = trees.one_shot_version_location(tree_name, relative=False)
    else:
        tree_folder = trees.regular_version_location(tree_name, relative=False)
    if os.access(tree_folder, os.F_OK):
        raise ValueError(f"Version tree {tree_name!r} already exists in {tree_folder}")

    cfg = config.SmigAlembicConfig.from_mig_path(mig_path, single_tree=tree_name)

    # may need to initialize the whole shebang
    alembic_folder = trees.alembic_folder(relative=False)
    if not os.access(alembic_folder, os.F_OK):

        _LOG.debug("Creating new alembic folder %r", alembic_folder)

        # initialize tree folder
        template = "generic"
        command.init(cfg, directory=alembic_folder, template=template)

    # create initial branch revision in a separate folder
    message = f"This is an initial pseudo-revision of the {tree_name!r} tree."
    rev_id = migrate.rev_id(manager)
    command.revision(cfg, head="base", rev_id=rev_id, branch_label=manager,
                     version_path=tree_folder, message=message)
