#!/bin/bash

# regular history
butler migrate-add-tree attributes
butler migrate-revision attributes DefaultButlerAttributeManager 1.0.0

butler migrate-add-tree collections
butler migrate-revision collections NameKeyCollectionManager 0.1.0
butler migrate-revision collections NameKeyCollectionManager 0.2.0
butler migrate-revision collections NameKeyCollectionManager 0.3.0
butler migrate-revision collections NameKeyCollectionManager 1.0.0
butler migrate-revision collections NameKeyCollectionManager 2.0.0
butler migrate-revision collections SynthIntKeyCollectionManager 0.1.0
butler migrate-revision collections SynthIntKeyCollectionManager 0.2.0
butler migrate-revision collections SynthIntKeyCollectionManager 0.3.0
butler migrate-revision collections SynthIntKeyCollectionManager 1.0.0
butler migrate-revision collections SynthIntKeyCollectionManager 2.0.0

butler migrate-add-tree dimensions
butler migrate-revision dimensions StaticDimensionRecordStorageManager 0.1.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 0.2.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 1.2.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 2.2.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 3.2.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 4.0.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 5.0.0
butler migrate-revision dimensions StaticDimensionRecordStorageManager 6.0.0

butler migrate-add-tree datasets
butler migrate-revision datasets ByDimensionsDatasetRecordStorageManager 0.1.0
butler migrate-revision datasets ByDimensionsDatasetRecordStorageManager 0.2.0
butler migrate-revision datasets ByDimensionsDatasetRecordStorageManager 0.3.0
butler migrate-revision datasets ByDimensionsDatasetRecordStorageManager 1.0.0
butler migrate-revision datasets ByDimensionsDatasetRecordStorageManagerUUID 1.0.0

butler migrate-add-tree opaque
butler migrate-revision opaque ByNameOpaqueTableStorageManager 0.1.0
butler migrate-revision opaque ByNameOpaqueTableStorageManager 0.2.0

butler migrate-add-tree datastores
butler migrate-revision datastores MonolithicDatastoreRegistryBridgeManager 0.1.0
butler migrate-revision datastores MonolithicDatastoreRegistryBridgeManager 0.2.0

# special one-shot history
butler migrate-add-tree --one-shot datasets/int_1.0.0_to_uuid_1.0.0
butler migrate-revision --one-shot datasets/int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManager 1.0.0
butler migrate-revision --one-shot datasets/int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManagerUUID 1.0.0

butler migrate-add-tree --one-shot datasets/int_0.3.0_to_uuid_1.0.0
butler migrate-revision --one-shot datasets/int_0.3.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManager 0.3.0
butler migrate-revision --one-shot datasets/int_0.3.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManagerUUID 1.0.0
