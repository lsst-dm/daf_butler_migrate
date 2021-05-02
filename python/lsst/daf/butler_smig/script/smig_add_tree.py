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

"""Dump configuration.
"""

from __future__ import annotations

import logging
import os

from alembic import command

from .. import config, smig


_LOG = logging.getLogger(__name__.partition(".")[2])


def smig_add_tree(tree_name: str, mig_path: str, one_shot: bool) -> None:
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
    """

    # check that its folder does not exist yet
    extra_tree_name = tree_name
    if one_shot:
        extra_tree_name = os.path.join("_oneshot", tree_name)
    tree_folder = os.path.join(mig_path, extra_tree_name)
    if os.access(tree_folder, os.F_OK):
        raise ValueError(f"Version tree {tree_name!r} already exists in {tree_folder}")

    # If we need to call init then we want location of generated INI file
    # to be outside of current folder
    cfg = config.SmigAlembicConfig.from_mig_path(mig_path, extra_tree_name=extra_tree_name)

    # may need to initialize the whole shebang
    alembic_folder = os.path.join(mig_path, "_alembic")
    if not os.access(alembic_folder, os.F_OK):

        _LOG.debug("Creating new alembic folder %r", alembic_folder)

        # initialize tree folder
        template = "generic"
        command.init(cfg, directory=alembic_folder, template=template)

    # create initial branch revision in a separate folder
    message = f"This is an initial pseudo-revision of the {tree_name!r} tree."
    rev_id = smig.rev_id(tree_name)
    command.revision(cfg, head="base", rev_id=rev_id, branch_label=tree_name,
                     version_path=tree_folder, message=message)
