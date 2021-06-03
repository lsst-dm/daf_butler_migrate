#!/bin/bash
#
# Script to automate schema migration of a single repo, migrating datasets
# tables from integer dataset IDs to UUIDs.
#
# Tested with these arguments:
#
# For ccso repo:
#    ./migrate_uuid.sh -d <folder> <repo> raw
# For teststand repo:
#    ./migrate_uuid.sh -d <folder> <repo> raw
# For main repo:
#    ./migrate_uuid.sh -d <folder> -c LSSTComCam/raw/all <repo> raw flat visitSummary deepCoadd
# For dc2 repo:
#    ./migrate_uuid.sh -d <folder> -c 2.2i/raw/test-med-1 <repo> raw flat visitSummary deepCoadd
#

# stop on any error
set -e

usage() {
    cat <<USAGE

Migrate single gen3 repository from integer to UUID dataset IDs.

Usage: $0 [-h] [-d <path>] <repo> [dataset_type ...]

Parameters:

    repo
        Path to repository, either directory containing butler.yaml file or
        name of the YAML file with butler configuration.

    dataset_type
        One or more dataset type names, for each dataset type the script will
        dump datasets for corresponding dataset type before and after migration
        and compare their contents.

Options:

    -h
        Print this usage and exit.

    -d <path>
        Folder name to store dumps of the datasets if dataset_type is
        specified. If folder does not exist it will be created. Default value
        for this option is "./migrate_uuid"

    -c <collection>
        Collection name for "raw" dataset type. This is only used if "raw"
        dataset type is specified as an argument. Limits the selection of raw
        datasets used for validation to this specific collection (neded to
        reduce selection time for large repos). Non-raw dataset types are not
        restricted to this collection.

USAGE
}

timestamp() {
    date "+%Y-%m-%dT%H:%M:%S"
}

# dump_datasets <repo> <dataset_type>
dump_datasets() {
    if [ "$2" = "raw" -a -n "$raw_collection" ]; then
        butler query-datasets --collections "$raw_collection" $1 $2
    else
        butler query-datasets $1 $2
    fi
}

# check_uuid_type <file> <uuid-type>
check_uuid_type() {
    cat "$1" | gawk -v UUID=$2 '
        $3 ~ /[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}/ {
            split($3, fields, "-");
            if (substr(fields[3], 1, 1) != UUID) {
                print "Unexpected UUID type:" $3;
                exit 1
            }
        }
'
}

folder="migrate_uuid"
raw_collection=""

while getopts hd:c: arg; do
    case "$arg" in
        h)
            usage
            exit
            ;;
        d)
            folder="${OPTARG}"
            ;;
        c)
            raw_collection="${OPTARG}"
            ;;
        ?)
            usage 1>&2
            exit 1
            ;;
    esac
done

shift $(( OPTIND - 1 ))
repo="$1"
shift
dataset_types="$@"

if [ -z "$repo" ]; then
    echo "ERROR: Required repository parameter is missing" 1>&2
    usage 1>&2
    exit 1
fi
# we need actual file name
if [ -d "$repo" ]; then
    repo="$repo/butler.yaml"
fi
if [ ! -f "$repo" ]; then
    echo "ERROR: repository '"$repo"' does not exist" 1>&2
    exit 1
fi
# check that butler.yaml is writable and has configured manager
if [ ! -w "$repo" ]; then
    echo "ERROR: repository '"$repo"' is not witable" 1>&2
    exit 1
fi
if ! egrep -q "^ *datasets:.*ByDimensionsDatasetRecordStorageManager *$" < "$repo" ; then
    echo "ERROR: butler config '"$repo"' has no ByDimensionsDatasetRecordStorageManager datasets manager configured" 1>&2
    exit 1
fi

# Check that butler has expected version of manager
echo "[progress] $(timestamp) Checking current version of dataset manager"
butler_version=$(butler migrate show-current "$repo" --butler | grep -E '^datasets:')
expect="datasets: lsst.daf.butler.registry.datasets.byDimensions._manager.ByDimensionsDatasetRecordStorageManager 1.0.0 -> 635083325f20"
if [ -z "$butler_version" ] ; then
    echo "ERROR: Failed to determine current version of datasets manager" 1>&2
    exit 1
elif [ "$butler_version" != "$expect" ] ; then
    echo "ERROR: Unexpected version of datasets manager:" 1>&2
    echo "ERROR:   expected: $expect" 1>&2
    echo "ERROR:   current : $butler_version" 1>&2
    exit 1
fi

# dump all datasets
for dataset_type in $dataset_types; do
    echo "[progress] $(timestamp) Dumping before-migration contents of $dataset_type datasets"
    mkdir -p "$folder"
    out="$folder/datasets-$dataset_type-before.txt"
    if ! dump_datasets $repo $dataset_type > $out; then
        echo "ERROR: Failed to dump datasets for dataset type $dataset_type to $out" 1>&2
        exit 1
    fi
done

# initialize alembic versions, safe to call even if already exists
echo "[progress] $(timestamp) Creating/updating alembic_version table"
butler migrate stamp "$repo"

# Ready for migration, go get some coffee
echo "[progress] $(timestamp) Running schema migration"
butler --log-level debug --long-log migrate upgrade --one-shot-tree datasets/int_1.0.0_to_uuid_1.0.0 "$repo" 2101fbf51ad3
echo "[progress] $(timestamp) Finished schema migration"

# update butler config
echo "[progress] $(timestamp) Updating butler configuration"
sed --in-place=.bck 's/ByDimensionsDatasetRecordStorageManager/ByDimensionsDatasetRecordStorageManagerUUID/' $repo

# dump all datasets again
for dataset_type in $dataset_types; do
    echo "[progress] $(timestamp) Dumping after-migration contents of $dataset_type datasets"
    mkdir -p "$folder"
    out="$folder/datasets-$dataset_type-after.txt"
    if ! dump_datasets $repo $dataset_type > $out; then
        echo "ERROR: Failed to dump datasets for dataset type $dataset_type to $out" 1>&2
        exit 1
    fi
done

# do some validation
status=0
for dataset_type in $dataset_types; do

    before="$folder/datasets-$dataset_type-before.txt"
    after="$folder/datasets-$dataset_type-after.txt"

    if [ "$dataset_type" = "raw" ]; then
        uuid=5
    else
        uuid=4
    fi
    echo "[progress] $(timestamp) Checking UUID type for $dataset_type"
    if ! check_uuid_type $after $uuid; then
        # complain but don't stop here
        echo "[progress] $(timestamp) UUID type check failed for $after"
        status=1
    fi

    # drop dataset ID from each file and compare
    echo "[progress] $(timestamp) comparing before/after contents for $dataset_type"
    if ! cmp -s <(gawk '{$3 = "_"; print}' < $before | sort) <(gawk '{$3 = "_"; print}' < $after | sort); then
        # complain but don't stop here
        echo "[progress] $(timestamp) validation failed for $dataset_type (comparing $before and $after)"
        status=1
    fi

done

if [ $status -ne 0 ]; then
    echo "ERROR: validation failed" 1>&2
    exit $status
else
    echo "[progress] $(timestamp) Success"
fi
