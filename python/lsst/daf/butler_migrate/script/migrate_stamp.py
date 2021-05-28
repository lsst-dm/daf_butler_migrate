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
from typing import Dict

from alembic import command

from .. import config, migrate


_LOG = logging.getLogger(__name__)


def migrate_stamp(repo: str, mig_path: str, purge: bool, dry_run: bool) -> None:
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
    """
    db_url, schema = migrate.butler_db_params(repo)

    manager_versions = migrate.manager_versions(db_url, schema)

    revisions: Dict[str, str] = {}
    for manager, (klass, version) in manager_versions.items():
        # for hash we use class name without module
        klass = klass.rpartition(".")[-1]
        rev_id = migrate.rev_id(manager, klass, version)
        _LOG.debug("found revision (%s, %s, %s) -> %s", manager, klass, version, rev_id)
        revisions[manager] = rev_id

    cfg = config.MigAlembicConfig.from_mig_path(mig_path)
    cfg.set_main_option("sqlalchemy.url", db_url)
    if schema:
        cfg.set_section_option("daf_butler_migrate", "schema", schema)

    if dry_run:
        print("Will store these revisions in alembic version table:")
        for manager, rev_id in revisions.items():
            print(f"  {manager}: {rev_id}")
    else:
        for revision in revisions.values():
            command.stamp(cfg, revision, purge=purge)
