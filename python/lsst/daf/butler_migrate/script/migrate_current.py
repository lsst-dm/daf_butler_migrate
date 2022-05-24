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


def migrate_current(repo: str, mig_path: str, verbose: bool, butler: bool, namespace: Optional[str]) -> None:
    """Display current revisions for a database.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.
    mig_path : `str`
        Filesystem path to location of revisions.
    verbose : `bool`
        Print verbose information if this flag is true.
    butler: `bool`
        If True then print versions numbers from butler, otherwise display
        information about alembic revisions.
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

    if butler:
        # Print current versions defined in butler.
        manager_versions = db.manager_versions(namespace)
        if manager_versions:
            for manager, (klass, version, rev_id) in sorted(manager_versions.items()):
                print(f"{manager}: {klass} {version} -> {rev_id}")
        else:
            print("No manager versions defined in butler_attributes table.")
    else:
        # Revisions from alembic
        cfg = config.MigAlembicConfig.from_mig_path(mig_path, db=db)
        command.current(cfg, verbose=verbose)

    # complain if alembic_version table is there but does not match manager
    # versions
    if db.alembic_revisions():
        db.validate_revisions(namespace)
