###############################
Migrations for datasets manager
###############################

The ``datasets`` tree has two branches:

- ``datasets-ByDimensionsDatasetRecordStorageManager`` which is the older implementation of the manager using integer dataset IDs.
- ``datasets-ByDimensionsDatasetRecordStorageManagerUUID`` which is the new implementation using UUIDs.

The regular revision tree has migrations defined for all manager versions that have existed in our code, but none of these migrations were actually implemented.

There is a one-shot migration implemented for migration from ``ByDimensionsDatasetRecordStorageManager`` 1.0.0 to ``ByDimensionsDatasetRecordStorageManagerUUID`` 1.0.0::

    $ butler migrate show-history --one-shot
    635083325f20 -> 2101fbf51ad3 (datasets) (head), Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.
    059cc7b7ef13 -> 635083325f20 (datasets), Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.
    <base> -> 059cc7b7ef13 (datasets), This is an initial pseudo-revision of the 'datasets/int_1.0.0_to_uuid_1.0.0' tree.

The migration script for this one-shot migration is in `2101fbf51ad3.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/_oneshot/datasets/int_1.0.0_to_uuid_1.0.0/2101fbf51ad3.py>`_.
