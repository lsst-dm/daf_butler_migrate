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

"""Display current revisions for a database."""

from __future__ import annotations

import logging

from .. import butler_attributes, database

_LOG = logging.getLogger(__name__)


def migrate_set_namespace(repo: str, namespace: str | None, update: bool) -> None:
    """Display current revisions for a database.

    Parameters
    ----------
    repo : `str`
        Path to butler configuration YAML file or a directory containing a
        "butler.yaml" file.
    namespace : `str`, optional
        Dimensions namespace to set, if `None` then existing namespace is
        printed.
    update : `bool`
        Allows update of the existing namespace.
    """
    db = database.Database.from_repo(repo)
    db_namespace = db.dimensions_namespace()

    if not namespace:
        # Print current value
        if not db_namespace:
            print("No namespace defined in dimensions configuration.")
        else:
            print("Current dimensions namespace:", db_namespace)

    else:
        if db_namespace and not update:
            raise ValueError(
                f"Namespace is already defined ({db_namespace}), use --update option to replace it."
            )

        def update_namespace(config: dict) -> dict:
            """Update namespace attribute"""
            config["namespace"] = namespace
            return config

        with db.connect() as connection:
            attributes = butler_attributes.ButlerAttributes(connection, db.schema)
            attributes.update_dimensions_json(update_namespace)
