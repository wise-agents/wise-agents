#!/bin/bash
# This script is used to run pgvector in a container

# define these variables before running the script
export POD_CONTAINER="${POD_CONTAINER:-docker}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export POSTGRES_DB="${POSTGRES_DB:-postgres}"

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
if [ -f ./.env ]; then
	. ./.env
fi

echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER run --rm --name vectordb -e POSTGRES_USER=$POSTGRES_USER -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD -e POSTGRES_DB=$POSTGRES_DB -p 6024:5432 -d pgvector/pgvector:pg16
