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

from alembic import command

from .. import config, migrate


_LOG = logging.getLogger(__name__)


def migrate_current(repo: str, mig_path: str, verbose: bool, butler: bool) -> None:
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
    """
    db_url, schema = migrate.butler_db_params(repo)

    if butler:
        # Print current versions defined in butler.
        manager_versions = migrate.manager_versions(db_url, schema)
        if manager_versions:
            for manager, (klass, version) in sorted(manager_versions.items()):
                rev_id = migrate.rev_id(manager, klass.rpartition(".")[-1], version)
                print(f"{manager}: {klass} {version} -> {rev_id}")
        else:
            print("No manager versions defined in butler_attributes table.")
    else:
        # Revisions from alembic
        cfg = config.SmigAlembicConfig.from_mig_path(mig_path)
        cfg.set_main_option("sqlalchemy.url", db_url)
        if schema:
            cfg.set_section_option("daf_butler_migrate", "schema", schema)
        command.current(cfg, verbose=verbose)
