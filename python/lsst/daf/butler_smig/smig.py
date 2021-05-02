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

import os
import uuid
from typing import Dict, List, Mapping, Tuple

import sqlalchemy

from lsst.daf.butler import ButlerConfig
from lsst.daf.butler.core.repoRelocation import replaceRoot


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


def butler_db_url(repo: str) -> str:
    """Extract registry database URL from Butler configuration.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.

    Returns
    -------
    db_url : `str`
        URL for registry database.
    """
    butlerConfig = ButlerConfig(repo)
    if "root" in butlerConfig:
        butlerRoot = butlerConfig["root"]
    else:
        butlerRoot = butlerConfig.configDir
    db_url = replaceRoot(butlerConfig["registry", "db"], butlerRoot)

    return db_url


def manager_versions(db_url: str) -> Mapping[str, Tuple[str, str]]:
    """Retrieve current manager versions stored in butler_attributes table.

    Parameters
    ----------
    db_url : `str`
        URL for registry database.

    Returns
    -------
    versions : `dict` [ `tuple` ]
        Mapping whose key is manager name (e.g. "datasets") and value is a
        tuple consisting of manager class name (including package/module) and
        version in X.Y.Z format.
    """
    engine = sqlalchemy.engine.create_engine(db_url)

    meta = sqlalchemy.schema.MetaData()
    table = sqlalchemy.schema.Table(
        "butler_attributes", meta,
        sqlalchemy.schema.Column("name", sqlalchemy.Text),
        sqlalchemy.schema.Column("value", sqlalchemy.Text),
    )

    # parse table contents into two separate maps
    managers: Dict[str, str] = {}
    versions: Dict[str, str] = {}
    sql = sqlalchemy.sql.select([table.columns.name, table.columns.value])
    with engine.connect() as connection:
        result = connection.execute(sql)
        for name, value in result:
            if name.startswith("config:registry.managers."):
                managers[name.rpartition(".")[-1]] = value
            elif name.startswith("version:"):
                versions[name.partition(":")[-1]] = value

    # combine them into one structure
    revisions: Dict[str, Tuple[str, str]] = {}
    for manager, klass in managers.items():
        version = versions.get(klass)
        if version:
            revisions[manager] = (klass, version)

    return revisions
