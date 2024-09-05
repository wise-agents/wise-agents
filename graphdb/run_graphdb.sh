#!/bin/bash
# This script is used to run the graph database

# It reads the username, password, and database name from the environment variables.
export POD_CONTAINER="${POD_CONTAINER:-docker}"
export NEO4J_USERNAME="${NEO4J_USERNAME:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-neo4jpassword}"
export NEO4J_DATABASE="${NEO4J_DATABASE:-neo4j}"

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
WORKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -f $WORKING_DIR/.env ]; then
       . $WORKING_DIR/.env
fi

echo "Neo4j Username: $NEO4J_USERNAME"
echo "Neo4j Password: $NEO4J_PASSWORD"
echo "Neo4j Database: $NEO4J_DATABASE"
echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER run --name neo4j --restart always --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=$NEO4J_USERNAME/$NEO4J_PASSWORD -e NEO4J_PLUGINS=\[\"apoc\"\] neo4j:5.21.0
