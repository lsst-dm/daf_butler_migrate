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

from __future__ import annotations

__all__ = ["update_day_obs"]

import logging
from typing import Any

from lsst.daf.butler import Butler, DimensionRecord
from lsst.utils import doImportType
from lsst.utils.iteration import chunk_iterable

_LOG = logging.getLogger(__name__)


def updated_record(rec: DimensionRecord, **kwargs: Any) -> DimensionRecord:
    """Create a new record with modified fields.

    Parameters
    ----------
    rec : `lsst.daf.butler.DimensionRecord`
        Record to be cloned.
    **kwargs : `typing.Any`
        Values to modify on copy. The keys must be known to the record.

    Returns
    -------
    new : `lsst.daf.butler.DimensionRecord`
       New record with updated values.
    """
    d = rec.toDict()
    # Should validate but this is not a general function for now.
    d.update(kwargs)
    return type(rec)(**d)


def update_day_obs(repo: str, instrument: str) -> None:
    """Update the day_obs for the given instrument.

    Parameters
    ----------
    repo : `str`
        URI of butler repository to update.
    instrument : `str`
        Name of instrument to use to update records.

    Notes
    -----
    This update code depends on being able to import the python instrument
    class registered with the instrument record.
    """
    # Connect to the butler.
    with Butler.from_config(repo, writeable=True) as butler:
        _update_day_obs(butler, instrument)


def _update_day_obs(butler: Butler, instrument: str) -> None:
    """Update day obs by taking Butler rather than repo string.

    Parameters
    ----------
    butler : `lsst.daf.butler.Butler`
        Butler repository to update.
    instrument : `str`
        Name of instrument to use to update records.
    """
    # Need the instrument class, since that is used to calculate day_obs.
    # Do not depend directly on pipe_base but to load this class pipe_base
    # will have to be available.
    instr_records = list(butler.registry.queryDimensionRecords("instrument", instrument=instrument))
    if len(instr_records) != 1:
        if not instr_records:
            raise RuntimeError(f"Unable to find an instrument record for instrument named {instrument}.")
        else:
            raise AssertionError(f"Impossibly got more than one instrument record named {instrument}.")
    instrument_class_name = instr_records[0].class_name
    instrument_cls = doImportType(instrument_class_name)
    instr = instrument_cls()
    translator = instr.translatorClass
    if translator is None:
        raise RuntimeError(
            f"Instrument class {instrument_class_name} has no registered translator class."
            " Unable to calculate the correct observing day."
        )

    # The naive approach is to query all the records and recalculate the
    # day_obs and then update them all in one big transaction. This will
    # be fine for a small repo but catastrophic with millions of exposure
    # and visit records.
    exposures_to_be_updated = {}
    exposures = butler.registry.queryDimensionRecords("exposure", instrument=instrument)
    counter = 0
    for exp in exposures:
        offset = translator.observing_date_to_offset(exp.timespan.begin)
        day_obs = translator.observing_date_to_observing_day(exp.timespan.begin, offset)
        if day_obs != exp.day_obs:
            # Need to update the record. Immutable so need a copy.
            exposures_to_be_updated[exp.id] = updated_record(exp, day_obs=day_obs)
        counter += 1

    _LOG.info(
        "Number of exposure records needing to be updated: %d / %d", len(exposures_to_be_updated), counter
    )

    visits_to_be_updated = {}

    # Work out the visits that need to be updated given the exposures we have
    # updated. Chunk the queries.
    for exposure_ids in chunk_iterable(exposures_to_be_updated, chunk_size=1_000):
        # If there are modified exposures associated visits will have to be
        # located and updated.
        visit_defs = butler.registry.queryDimensionRecords(
            "visit_definition",
            where="exposure in (exps)",
            bind={"exps": list(exposure_ids)},
            instrument=instrument,
        )

        visit_to_exposure = {}
        for defn in visit_defs:
            # We do not need to store all the exposures along with the visit
            # since by definition a visit has the same day_obs across all
            # exposures.
            visit_to_exposure[defn.visit] = defn.exposure

        # Now retrieve that visits themselves.
        visits = butler.registry.queryDimensionRecords(
            "visit",
            where="visit in (visits)",
            bind={"visits": list(visit_to_exposure)},
            instrument=instrument,
        )

        for visit in visits:
            exposure_id = visit_to_exposure[visit.id]
            # Index by exposure ID for later batching of inserts.
            visits_to_be_updated[exposure_id] = updated_record(
                visit, day_obs=exposures_to_be_updated[exposure_id].day_obs
            )

    _LOG.info("Number of visit records needing to be updated: %d", len(visits_to_be_updated))

    # Batch inserts in smallish transactions so that on restart we will
    # be able to ignore records that have already been fixed. It is important
    # that visits are updated when the exposures are updated.
    counter = 0
    for exposure_ids in chunk_iterable(exposures_to_be_updated, chunk_size=1_000):
        with butler.transaction():
            counter += 1
            _LOG.info("Updating exposure/visit records (chunk %d)", counter)
            exposure_records = [exposures_to_be_updated[exposure_id] for exposure_id in exposure_ids]
            butler.registry.insertDimensionData("exposure", *exposure_records, replace=True)

            visit_records = [
                visits_to_be_updated[exposure_id]
                for exposure_id in exposure_ids
                if exposure_id in visits_to_be_updated
            ]
            # insertDimensionData results in skypix overlaps being recalculated
            # and re-inserted even though we are only changing one unrelated
            # item.
            butler.registry.insertDimensionData("visit", *visit_records, replace=True)

    return
