
################
General concepts
################

`Butler`_ software is an evolving system which is constantly improving.
A major component of Butler is the Registry database with a complex schema.
Sometimes changes in Butler code or configuration require corresponding updates to the database schema.
``daf_butler_migrate`` package implements a number of tools which facilitate the process of defining schema upgrades and applying those upgrades to existing databases.
Note that creating Registry database from scratch is not supported by this package, but instead should be done with Butler.
``daf_butler_migrate`` is based heavily on `Alembic`_ but adds a layer of abstractions to match Butler implementation concepts.


Managers and versions
=====================

Butler code responsible for database operations is split into multiple *manager classes*, each manager class controlling a part of the database schema.
For the purpose of ``daf_butler_migrate``, managers are identified by their *type* and Python class name, e.g. ``collections`` and ``NameKeyCollectionManager``.
There may be more than one class implementing the same manager interface or type, specific class is usually defined by Registry configuration.
As database schema for a particular manager evolves over time it is assigned new version.
For many managers the version is a string which follows semantic versioning convention (*MAJOR.MINOR.PATCH*), but there are also special cases when version number can be a simple integer number.
More information and motivation behind versioning appears in `DMTN-191`_.


Revisions
=========

Alembic schema management tools use *revisions* to define particular version of the schema, revision can be arbitrary string.
Most commonly in Alembic one revision is used for the whole database schema, but it is also possible to define multiple revisions for one schema, with each revision reflecting the state of some part of the schema.
Alembic itself has no knowledge of which tables correspond to which part of schema or revision, this mapping is responsibility of the migration scripts.
The only thing that Alembic records in its special ``alembic_version`` table is the current state of the schema as one or more revisions.

To use Alembic toolset we need to build a mapping between Butler versions and Alembic revisions.
While Alembic revisions can be arbitrary strings, their length is limited to 32 characters.
Alembic revisions could be constructed by concatenating manager class names and versions, but to avoid potential issues with very long strings, we construct Alembic revision as a hash of manager type, manager class name (excluding package and module name), and manager version.
For example, a ``NameKeyCollectionManager`` wch has manager type ``collections`` and version ``1.0.0`` will have Alembic revision ``5e75e5391603``, alembic will only ever know about this revision, but it does not care about Butler-specific names.

There are multiple types of managers in Registry and manager types may have more than one implementation.
To support this complex setup we use Alembic support for branches and multiple bases (`DMTN-191`_ covers it in more details).
Every manager type has its own history of revisions which is separate from other manager types.
To support multiple implementations (classes) of the same manager type the history can contain one or more branches (making it a tree).
The root of the manager type tree corresponds to a revision generated from just a manager type name (e.g. ``collections``) and it has a branch name of its type.
Each implementation class receives a separate branch which originates from the that root.
Alembic branch name of the implementation class is a combination of a type name and a class name (e.g. ``collections-NameKeyCollectionManager``).
Revisions corresponding to the versions of implementation class all belong to the branch of that class.

Here is an example of revision history (in reverse time order) for a ``collections`` manager type with two implementation classes, in a standard Alembic representation::

    $ butler migrate show-history collections
    97a6aabd8998 -> 8c57494cabcc (collections, collections-SynthIntKeyCollectionManager) (head), Migration script for SynthIntKeyCollectionManager 2.0.0.
    b4073b638219 -> 97a6aabd8998 (collections, collections-SynthIntKeyCollectionManager), Migration script for SynthIntKeyCollectionManager 1.0.0.
    1a93ca89bc27 -> b4073b638219 (collections, collections-SynthIntKeyCollectionManager), Migration script for SynthIntKeyCollectionManager 0.3.0.
    079a1bc77f25 -> 1a93ca89bc27 (collections, collections-SynthIntKeyCollectionManager), Migration script for SynthIntKeyCollectionManager 0.2.0.
    8d2e9de2f21f -> 079a1bc77f25 (collections, collections-SynthIntKeyCollectionManager), Migration script for SynthIntKeyCollectionManager 0.1.0.
    5e75e5391603 -> 93341d68b814 (collections-NameKeyCollectionManager, collections) (head), Migration script for NameKeyCollectionManager 2.0.0.
    e866114194e1 -> 5e75e5391603 (collections-NameKeyCollectionManager, collections), Migration script for NameKeyCollectionManager 1.0.0.
    3ce2d3adf1f5 -> e866114194e1 (collections-NameKeyCollectionManager, collections), Migration script for NameKeyCollectionManager 0.3.0.
    a56af31bd899 -> 3ce2d3adf1f5 (collections-NameKeyCollectionManager, collections), Migration script for NameKeyCollectionManager 0.2.0.
    8d2e9de2f21f -> a56af31bd899 (collections-NameKeyCollectionManager, collections), Migration script for NameKeyCollectionManager 0.1.0.
    <base> -> 8d2e9de2f21f (collections) (branchpoint), This is an initial pseudo-revision of the 'collections' tree.

In this listing ``<base>`` meas a special initial Alembic pseudo-revision, essentially an empty schema.
Revision ``8d2e9de2f21f`` is a root of the whole tree for ``collections`` manager type, and each class' branch originates from that root revision.
The ``(head)`` notifies the latest revision in a branch.

It must be noted that while logically these revisions and branches may look similar to other revision systems (e.g. ``git``), there are also significant differences in their behavior.
One example is that revisions "inherit" the names of the branches, this is why every revision in the above list has ``collections`` branch name associated with it, and one of the class branch names.
Another big difference is in howe Alembic handles branch merges, which requires use of special one-shot migrations for switching between implementation classes/branches (described below).


Migration scripts
=================

Alembic revision history is defined as a collection of migration scripts, which are Python scripts with predefined structure.
Every script represents a single step in migration tree and defines several attributes, two most important among them are its target revision and a parent (or "down") revision.
Alembic does not define a separate structure for describing migration trees, that structure is deduced from the whole collection of migration scripts by connecting their parent revisions with other scripts.
``daf_butler_migrate`` keeps the collection of migration scripts in ``migrations`` folder, with a separate sub-folder for each manager type.
New migration scripts are created by running ``butler migrate add-revision`` command with appropriate arguments.
CLI commands have an option to specify different location for migration scripts, if necessary.


One-shot migrations
===================

Switching between different implementations of manager type is not something that can be added directly to migration history, but it needs to be supported.
As an example imagine that we need to migrate our schema from NameKeyCollectionManager 1.0.0 to SynthIntKeyCollectionManager 2.0.0 (from above revision listing).
This means that we need to define a migration script from revision ``5e75e5391603`` to revision ``8c57494cabcc``.
That migration cannot be added to Alembic because it has no support for multi-parent migrations (there is support for branch merging but it does something different).

A workaround for that situation has been implemented as special "one-shot" migrations.
In one-shot mode the regular history (migration scripts) for a particular tree is hidden from Alembic and is replaced with a different migration history that contains only one specific migration between two revisions on different branches (or maybe even on the same branch).
Special one-shot migration scripts live in ``migrations/_oneshot`` folder, with each sub-folder representing one particular instance of those migrations.
CLI commands have a special option to switch to a one-shot migration trees instead of using regular history tree.


Alembic configuration
=====================

In addition to migration scripts Alembic is driven by its configuration.
Part of the Alembic configuration is generated by ``butler migrate`` commands based on command line options (e.g. connection to SQL database).
A remaining static part of the configuration is located in ``migrations/_alembic`` folder and includes:

- ``alembic.ini`` - file defining some configuration options,
- ``env.py`` - file with Python code managing database connection and schema options,
- ``script.py.mako`` - file which is a template for generating new migration scripts.


Special managers
================

Usual managers that control database schema are regular Python classes which define a number of database tables, and version numbers of those managers come from their source code.
Some aspects of the schema are determined by different entities, for example dimension configuration file determines schema of dimension tables.
Different configurations will result in different schema even with the same version of ``dimensions`` manager.

To handle this dynamic situation a special kind of manager types was introduced in ``daf_butler_migrate``.
This mechanism is implemented mostly on ``daf_butler_migrate`` side, ``daf_butler`` code has no corresponding classes for these special managers.
In case of dimensions configuration, new manager type name for it is ``dimensions-config``.
Configuration object defines its own version, in case of dimensions configuration this is a simple number.
In theory there could be more than one dimension configuration (in separate databases), to support separate revision branches for them they need to have a unique tag.
For dimensions configuration this tag also comes from configuration itself (starting with version 1), from its "namespace" tag.
Our standard dimension configuration that comes with ``daf_butler`` defines "daf_butler" as its namespace.

Similarly to regular managers we need to construct an Alembic revision for each configuration version.
For datasets configuration we use a combination of pseudo-manager type ("datasets-config"), the namespace ("daf_butler") and version number.

Here is an example of the revision history for this special manager::

    $ butler migrate show-history dimensions-config
    bf6308af80aa -> c5ae3a2cd7c2 (dimensions-config, dimensions-config-daf_butler) (head), Migration script for dimensions.yaml namespace=daf_butler version=3.
    380002bcbb26 -> bf6308af80aa (dimensions-config, dimensions-config-daf_butler), Migration script for dimensions.yaml namespace=daf_butler version=2.
    f3bcee34f344 -> 380002bcbb26 (dimensions-config, dimensions-config-daf_butler), Migration script for dimensions.yaml namespace=daf_butler version=1.
    3e2891b82110 -> f3bcee34f344 (dimensions-config, dimensions-config-daf_butler), Migration script for dimensions.yaml namespace=daf_butler version=0.
    <base> -> 3e2891b82110 (dimensions-config, dimensions-config-daf_butler), This is an initial pseudo-revision of the 'dimensions-config' tree.

A special ``obscore-config`` manager is defined in a very similar way to handle configuration for ``obscore`` manager.

These special managers do not have matching entries in ``butler_attributes`` table, instead this information is extracted from their corresponding configuration objects, which are also stored in the same table ``butler_attributes``.


.. _Butler: https://pipelines.lsst.io/modules/lsst.daf.butler/index.html
.. _Alembic: https://alembic.sqlalchemy.org/
.. _DMTN-191: https://dmtn-191.lsst.io/
