# This file is part of daf_butler.
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

__all__ = ("rewrite_sqlite_registry",)

import io
import logging
import os
import tempfile
from collections import defaultdict

from lsst.daf.butler import Butler, Config, DatasetAssociation, DatasetId, DatasetRef, SkyPixDimension
from lsst.daf.butler.datastores.fileDatastore import FileDatastore
from lsst.daf.butler.direct_butler import DirectButler
from lsst.daf.butler.registry import CollectionType
from lsst.daf.butler.registry.databases.sqlite import SqliteDatabase
from lsst.daf.butler.registry.sql_registry import SqlRegistry
from lsst.daf.butler.transfers import RepoExportContext
from lsst.resources import ResourcePath
from lsst.utils.introspection import get_class_of

log = logging.getLogger(__name__)


def rewrite_sqlite_registry(source: str) -> None:
    """Rewrite a SQLite registry as a new registry.

    * Create a new sqlite registry based on the current configuration.
    * Export all dimension records, dataset types, collection information
      and import into new registry.
    * Transfer datasets without moving them.
    * Move the original sqlite file and butler configuration to backup
      versions and replace with the modified files.

    Parameters
    ----------
    source : `str`
        URI to a SQLite butler repository.
    """
    # Create the source butler early so we can ask it questions
    # without assuming things.
    source_butler = Butler.from_config(source, writeable=False)
    assert isinstance(source_butler, DirectButler)
    assert isinstance(source_butler._registry, SqlRegistry), "Expecting SqlRegistry instance"

    # Check that we are really working with a SQLite database.
    if not isinstance(source_butler._registry._db, SqliteDatabase):
        raise RuntimeError("This command can only be used on SQLite registries.")

    # The source butler knows where its config came from.
    source_config_uri = source_butler._config.configFile
    assert source_config_uri is not None, "Config file must not be None"

    # We need to read just the local configuration and not the expanded
    # one.
    source_config = Config(source_config_uri)

    # Keep the source_config around since we will need to rewrite it
    # later. Work on a copy.
    config = Config(source_config_uri)

    # Assume that we are rewriting this with the current set of registry
    # managers so remove any.
    del config["registry", "managers"]

    # Delete the URI of the registry since we want an entirely new
    # entry.
    del config["registry", "db"]

    # Force the new temporary butler repo to have an explicit path
    # to the existing datastore.  This will only work for a FileDatastore
    # so try that and if it doesn't work warn but continue since either
    # this is a new type of datastore or a chained datastore of some kind.
    # For now only handle the simple case.
    # NOTE: Execution Butler creation has a similar problem with working
    # out how to refer back to the original datastore.
    if isinstance(source_butler._datastore, FileDatastore):
        roots = source_butler.get_datastore_roots()
        datastore_name, datastore_root = roots.popitem()
        config["datastore", "root"] = str(datastore_root)

        # Force the name of the datastore since that should not
        # change from the source (and will if set from root)
        config["datastore", "name"] = datastore_name
    else:
        log.warning(
            "Migration is designed for FileDatastore but encountered %s."
            " Attempting migration anyhow. It should work so long as <butlerRoot> is not used"
            " in config.",
            str(type(source_butler._datastore)),
        )

    # Create a temp directory for the temporary butler (put it inside
    # the existing repositor).
    root_dir = source_config_uri.dirname().ospath
    with tempfile.TemporaryDirectory(prefix="temp-butler-", dir=root_dir) as dest_dir:
        # Create a new butler with this config as the seed but ensuring that it
        # does not overwrite the datastore root.
        dest_config = Butler.makeRepo(
            dest_dir,
            config,
            dimensionConfig=source_butler.dimensions.dimensionConfig,
            forceConfigRoot=False,
        )

        # Create destination butler
        dest_butler = Butler.from_config(dest_config, writeable=True)
        assert isinstance(dest_butler, DirectButler)
        assert isinstance(dest_butler._registry, SqlRegistry), "Expecting SqlRegistry instance"
        assert isinstance(dest_butler._registry._db, SqliteDatabase), "Expecting SqliteDatabase instance"

        transfer_everything(source_butler, dest_butler)

        # Obtain the name of the sqlite file at the destination.
        assert dest_butler._registry._db.filename is not None, "Expecting non-None filename from registry"
        dest_registry_uri = ResourcePath(dest_butler._registry._db.filename)

        # Finished with writing to the destination butler so
        # delete the variable to ensure we can't do any more.
        del dest_butler

        # Now need to move this registry to the original location
        # and move the existing registry to a backup.

        # Relocate the source registry first
        assert source_butler._registry._db.filename is not None, "Expecting non-None filename from registry"
        source_registry_uri = ResourcePath(source_butler._registry._db.filename)
        new_basename = "original_" + source_registry_uri.basename()
        backup_registry_uri = source_registry_uri.updatedFile(new_basename)
        os.rename(source_registry_uri.ospath, backup_registry_uri.ospath)

        # Move the new registry into the old location.
        os.rename(dest_registry_uri.ospath, source_registry_uri.ospath)

        # Rename the butler yaml file.
        backup_config_uri = source_config_uri.updatedFile("original_butler.yaml")
        os.rename(source_config_uri.ospath, backup_config_uri.ospath)

        # Change the managers in the source config.
        source_config["registry", "managers"] = dest_config["registry", "managers"]

        # and write a new config to the original location
        source_config.dumpToUri(source_config_uri)

    print(f"Successfully rewrote registry for butler at {source_config_uri}")


def transfer_everything(source_butler: DirectButler, dest_butler: DirectButler) -> None:
    """Transfer all content from one butler to another butler.

    Assumes that both registries have a common dimension universe.

    Parameters
    ----------
    source_butler : `~lsst.daf.butler.direct_butler.DirectButler`
        Butler to use as a source of information.
    dest_butler : `~lsst.daf.butler.direct_butler.DirectButler`
        Butler to receive all the content.
    """
    # Read all the datasets we are going to transfer, removing duplicates.
    # This set could be extremely large.  For now assume this is a small
    # to medium-sized registry.
    source_refs = set(source_butler.registry.queryDatasets(..., collections=...))

    # Import the data to the new butler
    transfer_non_datasets(source_butler, dest_butler)

    # If this is int to UUID we force "raw" to generate reproductible UUID.
    # If other raw-type datasets are to be supported the command will have
    # to take an additional parameter.
    dest_refs = dest_butler.transfer_from(source_butler, source_refs, skip_missing=False)

    # Map source ID to destination ID.
    source_to_dest = {source.id: dest for source, dest in zip(source_refs, dest_refs)}

    # Create any dataset associations
    create_associations(source_butler, dest_butler, source_to_dest)


def create_associations(
    source_butler: Butler, dest_butler: Butler, source_to_dest: dict[DatasetId, DatasetRef]
) -> None:
    """Create TAGGED and CALIBRATION collections in destination."""
    # For every dataset type in destination, get TAGGED and CALIBRATION
    # collection associations from the source, converting the source ID
    # to the correct destination ID.
    associations_by_collection = defaultdict(list)
    for datasetType in dest_butler.registry.queryDatasetTypes(...):
        collectionTypes = {CollectionType.TAGGED}
        if datasetType.isCalibration():
            collectionTypes.add(CollectionType.CALIBRATION)
        type_associations = source_butler.registry.queryDatasetAssociations(
            datasetType,
            collections=...,
            collectionTypes=collectionTypes,
            flattenChains=False,
        )
        for association in type_associations:
            dest_association = DatasetAssociation(
                ref=source_to_dest[association.ref.id],
                collection=association.collection,
                timespan=association.timespan,
            )
            associations_by_collection[association.collection].append(dest_association)

    # Update associations in the destination.
    for collection, associations in associations_by_collection.items():
        collection_type = dest_butler.registry.getCollectionType(collection)
        if collection_type == CollectionType.TAGGED:
            dest_butler.registry.associate(collection, [assoc.ref for assoc in associations])
        elif collection_type == CollectionType.CALIBRATION:
            refsByTimespan = defaultdict(list)
            for association in associations:
                refsByTimespan[association.timespan].append(association.ref)
            for timespan, refs in refsByTimespan.items():
                assert timespan is not None
                dest_butler.registry.certify(collection, refs, timespan)
        else:
            raise RuntimeError(
                f"Unexpected collection association for collection {collection}"
                f" of type {collection_type}."
            )


def transfer_non_datasets(source_butler: DirectButler, dest_butler: DirectButler) -> None:
    """Transfer everything that isn't related to datasets.

    Parameters
    ----------
    source_butler : `~lsst.daf.butler.direct_butler.DirectButler`
        Butler to extract information from.
    dest_butler : `~lsst.daf.butler.direct_butler.DirectButler`
        Destination butler.
    """
    # Use a string buffer to save on file I/O.  This might result in twice
    # the memory usage of using a file.
    yamlBuffer = io.StringIO()

    # Yaml is hard coded, since the class controls both ends of the
    # export/import.
    BackendClass = get_class_of(source_butler._config["repo_transfer_formats", "yaml", "export"])
    backend = BackendClass(yamlBuffer)
    exporter = RepoExportContext(
        source_butler._registry, source_butler.datastore, backend, directory=None, transfer=None
    )

    # Export all the collections.
    for c in source_butler.registry.queryCollections(..., flattenChains=True, includeChains=True):
        exporter.saveCollection(c)

    # Export all the dimensions.
    for dimension in source_butler.dimensions.getStaticElements():
        # Skip dimensions that are entirely derivable from other
        # dimensions or are sky pixelization.
        # eg "band" is always knowable from a "physical_filter".
        if isinstance(dimension, SkyPixDimension) or dimension.viewOf is not None:
            continue
        records = source_butler.registry.queryDimensionRecords(dimension)
        exporter.saveDimensionData(dimension, records)

    exporter._finish()

    # reset the string buffer to the beginning so the read operation will
    # actually *see* the data that was exported.
    yamlBuffer.seek(0)

    # Import the buffer.
    dest_butler.import_(filename=yamlBuffer, format="yaml")
