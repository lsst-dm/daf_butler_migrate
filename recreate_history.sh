#!/bin/bash

# regular history
butler smig-add-tree attributes
butler smig-revision attributes DefaultButlerAttributeManager 1.0.0

butler smig-add-tree collections
butler smig-revision collections NameKeyCollectionManager 0.1.0
butler smig-revision collections NameKeyCollectionManager 0.2.0
butler smig-revision collections NameKeyCollectionManager 0.3.0
butler smig-revision collections NameKeyCollectionManager 1.0.0
butler smig-revision collections NameKeyCollectionManager 2.0.0
butler smig-revision collections SynthIntKeyCollectionManager 0.1.0
butler smig-revision collections SynthIntKeyCollectionManager 0.2.0
butler smig-revision collections SynthIntKeyCollectionManager 0.3.0
butler smig-revision collections SynthIntKeyCollectionManager 1.0.0
butler smig-revision collections SynthIntKeyCollectionManager 2.0.0

butler smig-add-tree dimensions
butler smig-revision dimensions StaticDimensionRecordStorageManager 0.1.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 0.2.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 1.2.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 2.2.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 3.2.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 4.0.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 5.0.0
butler smig-revision dimensions StaticDimensionRecordStorageManager 6.0.0

butler smig-add-tree datasets
butler smig-revision datasets ByDimensionsDatasetRecordStorageManager 0.1.0
butler smig-revision datasets ByDimensionsDatasetRecordStorageManager 0.2.0
butler smig-revision datasets ByDimensionsDatasetRecordStorageManager 0.3.0
butler smig-revision datasets ByDimensionsDatasetRecordStorageManager 1.0.0
butler smig-revision datasets ByDimensionsDatasetRecordStorageManagerUUID 1.0.0

butler smig-add-tree opaque
butler smig-revision opaque ByNameOpaqueTableStorageManager 0.1.0
butler smig-revision opaque ByNameOpaqueTableStorageManager 0.2.0

butler smig-add-tree datastores
butler smig-revision datastores MonolithicDatastoreRegistryBridgeManager 0.1.0
butler smig-revision datastores MonolithicDatastoreRegistryBridgeManager 0.2.0

# special one-shot history
butler smig-add-tree --one-shot datasets_int_1.0.0_to_uuid_1.0.0
butler smig-revision --one-shot datasets_int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManager 1.0.0
butler smig-revision --one-shot datasets_int_1.0.0_to_uuid_1.0.0 ByDimensionsDatasetRecordStorageManagerUUID 1.0.0
