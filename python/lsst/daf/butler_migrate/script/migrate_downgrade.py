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

"""Display current revisions for a database.
"""

from __future__ import annotations

import logging
from typing import Optional

from alembic import command

from .. import config, database

_LOG = logging.getLogger(__name__)


def migrate_downgrade(
    repo: str, revision: str, mig_path: str, one_shot_tree: str, sql: bool, namespace: Optional[str]
) -> None:
    """Downgrade schema to a specified revision.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.
    revision : `str`
        Target revision or colon-separated range for sql mode.
    mig_path : `str`
        Filesystem path to location of revisions.
    one_shot_tree : `str`
        Nфme of special one-shot tree, if empty use regular history.
    sql : `bool`
        If True dump SQL instead of executing migration on a database.
    namespace: `str`, optional
        Dimensions namespace to use when "namespace" key is not present in
        ``config:dimensions.json``.
    """
    db = database.Database.from_repo(repo)

    if namespace is None and db.dimensions_namespace() is None:
        raise ValueError(
            "The `--namespace` option is required when namespace is missing from"
            " stored dimensions configuration"
        )

    # Check that alembic versions exist in database, we do not support
    # migrations from empty state.
    if not db.alembic_revisions():
        raise ValueError(
            "Alembic version table does not exist, you may need to run `butler migrate stamp` first."
        )

    # check that alembic versions are consistent with butler
    db.validate_revisions(namespace)

    one_shot_arg: Optional[str] = None
    if one_shot_tree:
        one_shot_arg = one_shot_tree
    cfg = config.MigAlembicConfig.from_mig_path(mig_path, db=db, one_shot_tree=one_shot_arg)

    command.downgrade(cfg, revision, sql=sql)
