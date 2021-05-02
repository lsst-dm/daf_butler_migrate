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

"""Display current revisions for a database.
"""

from __future__ import annotations

import logging

from alembic import command

from .. import config, smig


_LOG = logging.getLogger(__name__.partition(".")[2])


def smig_upgrade(repo: str, revision: str, mig_path: str, sql: bool) -> None:
    """Upgrade schema to a specified revision.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.
    revision : `str`
        Target revision or colon-separated range for sql mode.
    mig_path : `str`
        Filesystem path to location of revisions.
    sql : `bool`
        If True dump SQL instead of executing migration on a database.
    """
    db_url = smig.butler_db_url(repo)

    cfg = config.SmigAlembicConfig.from_mig_path(mig_path)
    cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(cfg, revision, sql=sql)
