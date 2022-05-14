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
from typing import Dict, Optional

from alembic import command

from .. import config, database

_LOG = logging.getLogger(__name__)


def migrate_stamp(
    repo: str, mig_path: str, purge: bool, dry_run: bool, namespace: Optional[str], manager: Optional[str]
) -> None:
    """Stamp alembic revision table with current registry versions.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.
    mig_path : `str`
        Filesystem path to location of revisions.
    purge : `bool`
        Delete all entries in the version table before stamping.
    dry_run : `bool`
        Skip all updates.
    namespace: `str`, optional
        Dimensions namespace to use when "namespace" key is not present in
        ``config:dimensions.json``.
    manager: `str`, Optional
        Name of the manager to stamp, if `None` then all managers are stamped.
    """
    db = database.Database.from_repo(repo)

    if namespace is None and db.dimensions_namespace() is None:
        raise ValueError(
            "The `--namespace` option is required when namespace is missing from"
            " stored dimensions configuration"
        )

    manager_versions = db.manager_versions(namespace)

    revisions: Dict[str, str] = {}
    for mgr_name, (klass, version, rev_id) in manager_versions.items():
        _LOG.debug("found revision (%s, %s, %s) -> %s", mgr_name, klass, version, rev_id)
        revisions[mgr_name] = rev_id

    if manager:
        if manager not in revisions:
            raise ValueError(f"Unknown manager name {manager}")
        revisions = {manager: revisions[manager]}

    if dry_run:
        print("Will store these revisions in alembic version table:")
        for manager, rev_id in revisions.items():
            print(f"  {manager}: {rev_id}")
    else:
        cfg = config.MigAlembicConfig.from_mig_path(mig_path, db=db)
        for revision in revisions.values():
            command.stamp(cfg, revision, purge=purge)
