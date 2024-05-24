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

import difflib
import json
from typing import Literal

import yaml
from lsst.resources import ResourcePath


def historical_dimensions_resource(universe_version: int, namespace: str = "daf_butler") -> ResourcePath:
    """Return location of the dimensions configuration for a specific version.

    Parameters
    ----------
    universe_version : `int`
        Version number of the universe to be loaded.
    namespace : `str`, optional
        Configuration namespace.

    Returns
    -------
    path : `lsst.resources.ResourcePath`
        Location of the configuration, there is no guarantee that this resource
        actually exists.
    """
    return ResourcePath(
        f"resource://lsst.daf.butler/configs/old_dimensions/{namespace}_universe{universe_version}.yaml"
    )


def load_historical_dimension_universe_json(universe_version: int) -> str:
    """Load a specific version of the default dimension universe as JSON.

    Parameters
    ----------
    universe_version : `int`
        Version number of the universe to be loaded.

    Returns
    -------
    universe : `str`
        Dimension universe configuration encoded as a JSON string.
    """
    path = historical_dimensions_resource(universe_version)
    with path.open() as input:
        dimensions = yaml.safe_load(input)
    return json.dumps(dimensions)


def compare_json_strings(
    expected: str, actual: str, diff_style: Literal["unified", "ndiff"] = "unified"
) -> str | None:
    """Compare two JSON strings and return a human-readable description of
    the differences.

    Parameters
    ----------
    expected : `str`
        JSON-encoded string to use as the basis for comparison.
    actual : `str`
        JSON-encoded string to compare with the expected value.
    diff_style : "unified" | "ndiff"
        What type of diff to return.

    Returns
    -------
    diff : `str` | `None`
        If the two inputs parse as equivalent data, returns `None`.  If there
        are differences between the two inputs, returns a human-readable string
        describing the differences.
    """
    expected = _normalize_json_string(expected)
    actual = _normalize_json_string(actual)

    if expected == actual:
        return None

    if diff_style == "unified":
        diff = difflib.unified_diff(expected.splitlines(), actual.splitlines(), lineterm="")
    elif diff_style == "ndiff":
        diff = difflib.ndiff(expected.splitlines(), actual.splitlines())
    else:
        raise ValueError(f"Unknown {diff_style=}")
    return "\n".join(diff)


def _normalize_json_string(json_string: str) -> str:
    # Re-encode a JSON string in a standardized format with sorted keys.
    return json.dumps(json.loads(json_string), indent=2, sort_keys=True)
