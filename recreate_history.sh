#!/bin/bash

# regular history
butler migrate add-tree attributes
butler migrate add-revision attributes DefaultButlerAttributeManager 1.0.0

butler migrate add-tree collections
butler migrate add-revision collections NameKeyCollectionManager 0.1.0
butler migrate add-revision collections NameKeyCollectionManager 0.2.0
butler migrate add-revision collections NameKeyCollectionManager 0.3.0
butler migrate add-revision collections NameKeyCollectionManager 1.0.0
butler migrate add-revision collections NameKeyCollectionManager 2.0.0
butler migrate add-revision collections SynthIntKeyCollectionManager 0.1.0
butler migrate add-revision collections SynthIntKeyCollectionManager 0.2.0
butler migrate add-revision collections SynthIntKeyCollectionManager 0.3.0
butler migrate add-revision collections SynthIntKeyCollectionManager 1.0.0
butler migrate add-revision collections SynthIntKeyCollectionManager 2.0.0

butler migrate add-tree dimensions
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 0.1.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 0.2.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 1.2.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 2.2.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 3.2.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 4.0.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 5.0.0
butler migrate add-revision dimensions StaticDimensionRecordStorageManager 6.0.0

butler migrate add-tree datasets
butler migrate add-revision datasets ByDimensionsDatasetRecordStorageManager 0.1.0
butler migrate add-revision datasets ByDimensionsDatasetRecordStorageManager 0.2.0
butler migrate add-revision datasets ByDimensionsDatasetRecordStorageManager 0.3.0
butler migrate add-revision datasets ByDimensionsDatasetRecordStorageManager 1.0.0
butler migrate add-revision datasets ByDimensionsDatasetRecordStorageManagerUUID 1.0.0

butler migrate add-tree opaque
butler migrate add-revision opaque ByNameOpaqueTableStorageManager 0.1.0
butler migrate add-revision opaque ByNameOpaqueTableStorageManager 0.2.0

butler migrate add-tree datastores
butler migrate add-revision datastores MonolithicDatastoreRegistryBridgeManager 0.1.0
butler migrate add-revision datastores MonolithicDatastoreRegistryBridgeManager 0.2.0

# special one-shot history
butler migrate add-tree --one-shot datasets/int_1.0.0_to_uuid_1.0.0
butler migrate add-revision --one-shot datasets/int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManager 1.0.0
butler migrate add-revision --one-shot datasets/int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManagerUUID 1.0.0

# just another example
# butler migrate add-tree --one-shot datasets/int_0.3.0_to_uuid_1.0.0
# butler migrate add-revision --one-shot datasets/int_0.3.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManager 0.3.0
# butler migrate add-revision --one-shot datasets/int_0.3.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManagerUUID 1.0.0
