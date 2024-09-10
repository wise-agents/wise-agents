#!/bin/bash
# This script is used to run the redis database


# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
WORKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -f $WORKING_DIR/.env ]; then
       . $WORKING_DIR/.env
fi

# Check if the environment variables are set
echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER  run --restart always  -p 6379:6379 -p 8002:8001 redis/redis-stack:latest
