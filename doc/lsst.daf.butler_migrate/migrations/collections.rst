##################################
Migrations for collections manager
##################################

The ``collections`` tree has a number of migrations scripts created but there is no actual migration implemented in any of them.
These scripts reflect the history of versions that existed in ``daf_butler`` code, but all production version of database should have the latest version of the schema.
The ``collections`` tree has two branches, ``collections-SynthIntKeyCollectionManager`` and ``collections-NameKeyCollectionManager``, for two separate implementations.


One-shot migration to integer collection IDs
============================================

This is a one-shot migration from ``NameKeyCollectionManager`` 2.0.0 to ``SynthIntKeyCollectionManager`` 2.0.0::

    $ butler migrate show-history --one-shot collections/name_2.0.0_to_int_2.0.0
    93341d68b814 -> 8c57494cabcc (collections) (head), Migration script for SynthIntKeyCollectionManager 2.0.0.
    8d2e9de2f21f -> 93341d68b814 (collections), Migration script for NameKeyCollectionManager 2.0.0.
    <base> -> 8d2e9de2f21f (collections), Initial pseudo-revision of the 'collections/name_2.0.0_to_int_2.0.0' tree.

The migration script for this one-shot migration is in `8c57494cabcc.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/_oneshot/collections/name_2.0.0_to_int_2.0.0/8c57494cabcc.py>`_. JIRA ticket `DM-42076 <https://jira.lsstcorp.org/browse/DM-42076>`_ has extra info on performance of this migration on large repositories.
