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

from __future__ import annotations

from typing import List

import os
import uuid


_MIG_FOLDER_ENV = "DAF_BUTLER_SMIG_MIGRATIONS"
_SMIG_PACKAGE_ENV = "DAF_BUTLER_SMIG_DIR"

NS_UUID = uuid.UUID('840b31d9-05cd-5161-b2c8-00d32b280d0f')
"""Namespace UUID used for UUID5 generation. Do not change. This was
produced by `uuid.uuid5(uuid.NAMESPACE_DNS, "lsst.org")`.
"""

def migrations_folder() -> str:
    """Return default location of top-level folder containing all migrations.

    Returns
    -------
    path : `str`
        Location of top-level folder containing all migrations.
    """
    loc = os.environ.get(_MIG_FOLDER_ENV)
    if loc:
        return loc
    loc = os.environ.get(_SMIG_PACKAGE_ENV)
    if loc:
        return os.path.join(loc, "migrations")
    raise ValueError(f"None of {_MIG_FOLDER_ENV} or {_SMIG_PACKAGE_ENV} environment variables is defined")


def version_locations(mig_path: str, one_shot: bool = False) -> List[str]:
    """Return list of folders for version_locations.

    Parameters
    ----------
    mig_path : `str`
        Top-level folder with migrations.
    one_shot : `bool`
        If `True` return locations for special one-shot migrations.

    Returns
    -------
    names : `list` [ `str` ]
        String containing space-separated list of locations.
    """
    names: List[str] = []
    if one_shot:
        mig_path = os.path.join(mig_path, "_oneshot")
        # it may not exist, treat it as empty
        if not os.access(mig_path, os.F_OK):
            return names
    for entry in os.scandir(mig_path):
        if entry.is_dir() and entry.name not in ("_alembic", "_oneshot"):
            names.append(os.path.join(mig_path, entry.name))
    return names

def rev_id(*args: str) -> str:
    """Generate revision ID from arguments.

    Returned string is a determenistic hash of the arguments.

    Returns
    -------
    rev_id : `str`
        Revision ID, 12-character string.
    """
    name = "-".join(args)
    return uuid.uuid5(NS_UUID, name).hex[-12:]
