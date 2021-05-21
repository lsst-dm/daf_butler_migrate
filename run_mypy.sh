#!/bin/bash

# migration scripts have common names, need to run mypy separately on
# each migration tree
for f in python migrations/*; do
    echo Checking $f
    mypy $f
done
