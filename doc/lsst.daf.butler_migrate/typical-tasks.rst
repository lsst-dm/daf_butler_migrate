
#######################
Typical migration tasks
#######################

Ths page collects some examples of typical migration tasks with some explanation.
Examples below assume that ``REPO`` environment variable is set to a location of Butler repository (e.g. folder containing ``butler.yaml`` file)::

    REPO=/path/to/butler/repository

As ``daf_butler_migrate`` is not a part of the regular release it has to be checked out from Github::

    $ git clone git@github.com:lsst-dm/daf_butler_migrate
    $ cd daf_butler_migrate
    $ setup -k -r .
    $ scons

After this ``butler migrate`` command should be available for use.

Revision stamping
=================

Alembic depends on ``alembic_version`` table for knowing current revision(s) of database schema.
Database created by Butler initially does not include this table, but Butler stores current versions of its managers in its internal table ``butler_attributes``.
Before executing any other migration commands ``alembic_version`` table needs to be created with ``butler migrate stamp`` command.

To check the existence of  ``alembic_version`` table one can run the ``show-current`` command::

    $ butler migrate show-current $REPO

If its output is empty then ``alembic_version`` does not exist and has to be created and current revisions stamped into it with this command::

    $ butler migrate stamp $REPO

If the repository was created with an old version of dataset configuration that does not define ``namespace`` key, then it is necessary to pass namespace as a separate option on command line::

    $ butler migrate stamp --namespace=daf_butler $REPO

The ``daf_butler`` namespace is used for dimensions configuration that comes with regular ``daf_butler`` releases.
If repository dimensions are not compatible with regular ``daf_butler`` dimensions, different and unique name has to be used.

Alternatively (and preferably) to using ``--namespace`` option one can run ``set-namespace`` before ``stamp`` to add namespace to dimensions configuration::

    $ butler migrate set-namespace $REPO daf_butler
    $ butler migrate stamp $REPO

Once the revisions are stamped the ``show-current`` command should produce non-empty output::

    $ butler migrate show-current $REPO
    2101fbf51ad3 (head)
    8c57494cabcc (head)
    c5ae3a2cd7c2 (head)
    035dcf13ef18 (head)
    77e5b803ad3f (head)
    a07b3b60e369 (head)
    f22a777cf382 (head)


Checking schema revisions
=========================

Current revisions of the schema exist in two places in database.
Alembic revisions (hex strings) are stored in ``alembic_version`` table created by ``stamp`` command as described above.
Registry stores version numbers of its managers in ``butler_attributes`` table.
The ``show-current`` command displays versions/revisions from both these tables.

Without options it shows revisions from ``alembic_version`` table::

    $ butler migrate show-current $REPO
    c5ae3a2cd7c2 (head)
    8c57494cabcc (head)
    035dcf13ef18 (head)
    77e5b803ad3f (head)
    a07b3b60e369 (head)
    f22a777cf382 (head)
    2101fbf51ad3 (head)

Passing ``-v`` option to this command will show more verbose output that also includes location of migration script for that revision.
The ``(head)`` tag above means that this revision is the latest one in the revision history.
If ``(head)`` is missing then newer revisions exist in the revision history, and migrations can be performed on that tree.

With ``--butler`` option this command displays information from ``butler_attributes`` table::

    $ butler migrate show-current --butler $REPO
    attributes: lsst.daf.butler.registry.attributes.DefaultButlerAttributeManager 1.0.0 -> f22a777cf382
    collections: lsst.daf.butler.registry.collections.synthIntKey.SynthIntKeyCollectionManager 2.0.0 -> 8c57494cabcc
    datasets: lsst.daf.butler.registry.datasets.byDimensions._manager.ByDimensionsDatasetRecordStorageManagerUUID 1.0.0 -> 2101fbf51ad3
    datastores: lsst.daf.butler.registry.bridge.monolithic.MonolithicDatastoreRegistryBridgeManager 0.2.0 -> a07b3b60e369
    dimensions: lsst.daf.butler.registry.dimensions.static.StaticDimensionRecordStorageManager 6.0.2 -> 035dcf13ef18
    dimensions-config: daf_butler 3 -> c5ae3a2cd7c2
    opaque: lsst.daf.butler.registry.opaque.ByNameOpaqueTableStorageManager 0.2.0 -> 77e5b803ad3f

The output includes manager type name, its full class name (except for special ``dimensions-config`` manager), and its version number.
Revision number appearing here is calculated from those three items and it must match one of the revisions in ``alembic_version`` table.


Running schema upgrades
=======================

If database has an obsolete schema revision for one of the managers one can upgrade it by running migration script with ``upgrade`` command.
First step is to decide which migrations needs to be performed.
Suppose you look at the ``show-current`` output and noticed that it shows revision ``87a30df8c8c5`` without ``(head)``.
Looking at ``show-current --butler`` you can say that this revision belongs to ``dimensions`` manager with version ``6.0.0``.

To check which new revisions exist run ``show-history`` command for that manager::

    $ butler migrate show-history dimensions
    1601d5973bf8 -> 035dcf13ef18 (dimensions-StaticDimensionRecordStorageManager, dimensions) (head), Migration script for StaticDimensionRecordStorageManager 6.0.2.
    87a30df8c8c5 -> 1601d5973bf8 (dimensions-StaticDimensionRecordStorageManager, dimensions), Migration script for StaticDimensionRecordStorageManager 6.0.1.
    a1e0fefed6c7 -> 87a30df8c8c5 (dimensions-StaticDimensionRecordStorageManager, dimensions), Migration script for StaticDimensionRecordStorageManager 6.0.0.
    e45766f0daea -> a1e0fefed6c7 (dimensions-StaticDimensionRecordStorageManager, dimensions), Migration script for StaticDimensionRecordStorageManager 5.0.0.

You can tell that revision ``87a30df8c8c5`` can be upgraded to ``1601d5973bf8`` (version 6.0.1), and latter can be also upgraded to ``035dcf13ef18`` (version 6.0.2).

With Alembic each migration has to be performed as a separate step, providing an explicit revision number.
The two commands that perform upgrade to latest version 6.0.2 are::

    $ butler migrate upgrade $REPO 1601d5973bf8
    $ butler migrate upgrade $REPO 035dcf13ef18

After that ``show-current`` should show ``035dcf13ef18 (head)`` in its output.

Usually migration scripts are running in a single transaction, if migration fails for some reason, the state of the schema should remain unchanged.

Some migrations may require additional command line arguments which are passed via ``--options KEY=VALUE`` or ``--namespace NAMESPACE`` options.
Individual scripts detect when such options area necessary and will produce a message when options are missing.


Downgrading schema
==================

It is possible to also switch schema to a previous revision via ``downgrade`` command.
The command takes a revision number which should be a revision preceding the current one.
For example, to downgrade ``dimensions`` manager revision from current ``035dcf13ef18`` to previous ``1601d5973bf8`` run this command::

    $ butler migrate downgrade $REPO 1601d5973bf8

Of course, migration script has to implement ``downgrade()`` method for this, which may not be always true.
