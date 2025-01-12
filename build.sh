#!/bin/bash

# Run npm build first
if npm run build; then
    # If npm build succeeds, run uv build
    uv build --wheel
else
    # If npm build fails, exit with error code
    echo "npm build failed"
    exit 1
fi
