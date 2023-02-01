
#################
Migration scripts
#################

``daf_butler_migrate`` is also a repository of migration scripts located in ``migrations`` folder.
Each migration script represents a single edge in revision trees, Alembic uses these scripts to build a complete revision tree every time it runs.
Alembic itself does not know anything about migration process, it simply calls these script to perform actual migration steps (upgrades or downgrades).
The only thing that Alembic manages in the database itself is the contents of ``alembic_version`` table, which contains revision(s) of the current database schema.

Here is an example of contents of the ``migrations`` folder::

    $ ls -1 migrations/
    _alembic
    _oneshot
    attributes
    collections
    datasets
    datastores
    dimensions
    dimensions-config
    opaque

Many sub-folders there contain regular migration scripts for a corresponding tree (manager type), but there are two special sub-folders in it:

- ``_alembic`` which contains configuration template, ``env.py`` file used by Alembic and migration script template.
- ``_oneshot`` which contains sub-folders for special one-shot migration scripts.

Regular sub-folders contain a bunch of migration scripts, e.g.::

    $ ls -1 migrations/datasets/
    059cc7b7ef13.py
    2101fbf51ad3.py
    38a9414ea7a2.py
    576045cb7831.py
    635083325f20.py
    eb5a3cc76666.py

``butler migrate`` has a number of commands to visualize revision trees and create new migration scripts.
Below are some simple examples of the usage for these commands.


Display list of tree names
==========================

The command for that is ``butler migrate show-trees``, it just list the trees (manager type names) in the migrations folder, e.g.::

    $ butler migrate show-trees
    attributes
    collections
    datasets
    datastores
    dimensions
    dimensions-config
    opaque

With ``--one-shot`` option this command will show the names of the special one-shot trees, the names of the one-shot trees include manager type name and a unique identifier separated by slash::

    $ butler migrate show-trees --one-shot
    datasets/int_1.0.0_to_uuid_1.0.0


Display revision trees
======================

The ``butler migrate show-history`` will show complete revision history for all trees (excluding one-shot), which could be long.
Passing an optional tree name will limit output to just that manager type::

    $ butler migrate show-history datasets
    059cc7b7ef13 -> 2101fbf51ad3 (datasets, datasets-ByDimensionsDatasetRecordStorageManagerUUID) (head), Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.
    576045cb7831 -> 635083325f20 (datasets-ByDimensionsDatasetRecordStorageManager, datasets) (head), Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.
    38a9414ea7a2 -> 576045cb7831 (datasets-ByDimensionsDatasetRecordStorageManager, datasets), Migration script for ByDimensionsDatasetRecordStorageManager 0.3.0.
    eb5a3cc76666 -> 38a9414ea7a2 (datasets-ByDimensionsDatasetRecordStorageManager, datasets), Migration script for ByDimensionsDatasetRecordStorageManager 0.2.0.
    059cc7b7ef13 -> eb5a3cc76666 (datasets, datasets-ByDimensionsDatasetRecordStorageManager), Migration script for ByDimensionsDatasetRecordStorageManager 0.1.0.
    <base> -> 059cc7b7ef13 (datasets) (branchpoint), This is an initial pseudo-revision of the 'datasets' tree.

Option ``-v`` can be used with this and other commands to produce more detailed Alembic output.

Above output includes parent and target revisions for each script, list of branches, special tags (``head`` or ``branchpoint``), and a comment string as defined in a script.

Adding ``--one-shot`` option displays history for corresponding one-shot revision tree, or all trees::

    $ butler migrate show-history --one-shot datasets/int_1.0.0_to_uuid_1.0.0
    635083325f20 -> 2101fbf51ad3 (datasets) (head), Migration script for ByDimensionsDatasetRecordStorageManagerUUID 1.0.0.
    059cc7b7ef13 -> 635083325f20 (datasets), Migration script for ByDimensionsDatasetRecordStorageManager 1.0.0.
    <base> -> 059cc7b7ef13 (datasets), This is an initial pseudo-revision of the 'datasets/int_1.0.0_to_uuid_1.0.0' tree.

Note that branch name for the one-shot tree above is also ``datasets`` and it does not have any class-specific branches because it migrates schema across branches.
Typically output for ``--one-shot`` will include three lines per tree.
Two bottom lines are just placeholders that define tree structure and their corresponding scripts are empty and never executed.
Top line corresponds to actual migration script which migrates ``datasets`` schema from revision ``635083325f20`` to ``2101fbf51ad3``.
These two revisions exists in the regular tree output above and they correspond to different branches.


Add new revision tree
=====================

When new manager type is added to Butler (or a special pseudo-manager is defined in ``daf_butler__migrate``) its tree needs to be added to the list.
This is done with ``butler migrate add-tree`` command, e.g.::

    $ butler migrate add-tree obscore
      Creating directory .../daf_butler_migrate/migrations/obscore ...  done
      Generating .../daf_butler_migrate/migrations/obscore/f8b9756419bb.py ...  done

One-shot migration trees are added with ``--one-shot`` option, name of the tree is a combination of manager type and some unique string::

    $ butler migrate add-tree --one-shot obscore/pgshere_0.0.1_to_postgis_0.0.1
      Creating directory .../daf_butler_migrate/migrations/_oneshot/obscore/pgshere_0.0.1_to_postgis_0.0.1 ...  done
      Generating .../daf_butler_migrate/migrations/_oneshot/obscore/pgshere_0.0.1_to_postgis_0.0.1/8b8e030aba2b.py ...  done

The ``add-tree`` command creates corresponding folder inside ``migrations`` folder and adds a placeholder migration script to it.
This script is not used for actual migration, it defines tree root with a branch name corresponding to the manager name.

Add new revision
================

Adding new revision to an existing tree is done with the command ``butler migrate add-revision`` which takes tree name, manager class name, and a version::

    $ butler migrate add-revision obscore ObsCoreLiveTableManager 0.0.1
      Generating .../daf_butler_migrate/migrations/obscore/8f2a981dc7f0.py ...  done

Usually the initial version of the schema is added to database when Registry is created.
In that case there is no need to populate first migration script with actual migration code, e.g. ``8f2a981dc7f0.py`` script just created can be a placeholder and a starting point for defining other migrations.

Note that this tool does not care about ordering of semantic version number and it always uses latest ``(head)`` revision as a parent for new revision.

Similarly using ``--one-shot`` option will add migration steps to one-shot trees.
BEcause one-shot trees are used to migrate schema between existing revisions on different branches, one has to define a starting point for the parent revision and then add an actual migration script to a target revision.
E.g. assuming that both version already exists in regular ``obscore`` tree these to commands can be used to complete one-shot tree (this is completely fictional example)::

    $ butler migrate add-revision --one-shot obscore/pgshere_0.0.1_to_postgis_0.0.1 ObsCorePgSphereTableManager 0.0.1
      Generating .../daf_butler_migrate/migrations/_oneshot/obscore/pgshere_0.0.1_to_postgis_0.0.1/33ebc1f88427.py ...  done
    $ butler migrate add-revision --one-shot obscore/pgshere_0.0.1_to_postgis_0.0.1 ObsCorePostGisTableManager 0.0.1
      Generating .../daf_butler_migrate/migrations/_oneshot/obscore/pgshere_0.0.1_to_postgis_0.0.1/7a6e7f8efdc3.py ...  done

The actual migration script will be in ``_oneshot/obscore/pgshere_0.0.1_to_postgis_0.0.1/7a6e7f8efdc3.py``, and it has to be updated with actual migration code.


Edit migration script
=====================

Migration scripts contain some metadata used by Alembic and two methods -- ``upgrade()`` and ``downgrade()``.
Generated scripts have these two methods empty and at least the ``upgrade`` method needs to be implemented.
The ``downgrade`` method can be used for reverting migrations and it is also a good idea to implement it, if it can be reasonably done.
If ``downgrade`` method is not implemented then reverting migration will not be possible using ``butler migrate downgrade``.

Implementation of the two methods is not always trivial.
Good starting point for this is `Alembic`_ documentation and examples in existing migration scripts.


.. _Alembic: https://alembic.sqlalchemy.org/
