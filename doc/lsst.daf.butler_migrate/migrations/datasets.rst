###############################
Migrations for datasets manager
###############################

The ``datasets`` tree has two branches:

- ``datasets-ByDimensionsDatasetRecordStorageManager`` which is the older implementation of the manager using integer dataset IDs, this manager class was removed from the code starting with ``w_2023_10``.
- ``datasets-ByDimensionsDatasetRecordStorageManagerUUID`` which is the new implementation using UUIDs.

The regular revision tree has migrations defined for all manager versions that have existed in our code, but only few of these migrations were actually implemented.


One-shot migration to UUID
==========================

There is a one-shot migration implemented for migration from ``ByDimensionsDatasetRecordStorageManager`` 1.0.0 to ``ByDimensionsDatasetRecordStorageManagerUUID`` 1.0.0::

    $ butler migrate show-history --one-shot
    635083325f20 -> 2101fbf51ad3 (datasets) (head), Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.
    059cc7b7ef13 -> 635083325f20 (datasets), Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.
    <base> -> 059cc7b7ef13 (datasets), This is an initial pseudo-revision of the 'datasets/int_1.0.0_to_uuid_1.0.0' tree.

The migration script for this one-shot migration is in `2101fbf51ad3.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/_oneshot/datasets/int_1.0.0_to_uuid_1.0.0/2101fbf51ad3.py>`_.


ByDimensionsDatasetRecordStorageManagerUUID 1.0.0 to 2.0.0
==========================================================

Migration script: `4e2d7a28475b.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/datasets/4e2d7a28475b.py>`_

Changes the type of ``ingest_date`` column in ``dataset`` table from ``TIMESTAMP`` to ``BIGINT``, containing TAI nanoseconds since epoch like many other timestamp columns.

.. attention::
    This migration script uses an optimized technique for PostgreSQL to convert timestamps with a reasonable performance at large scale.
    The optimization uses a simplified in-exact approach for calculating TAI timestamp from UTC timestamp stored in database.
    This approach assumes that all ingest dates are reasonably recent and uses a fixed offset of 37 seconds between TAI and UTC.
    Non-PostgreSQL backends utilize more exact approach which is significantly slower.
