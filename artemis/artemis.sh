#!/bin/bash
# This script is used to run the artemis MQ broker in a container

# define these variables before running the script
#export POD_CONTAINER = podman | docker
export POD_CONTAINER="${POD_CONTAINER:-docker}"

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
WORKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -f $WORKING_DIR/../.env ]; then
	echo "Executing " $WORKING_DIR/../.env
	. $WORKING_DIR/../.env
fi
if [ -f $WORKING_DIR/.env ]; then
	echo "Executing " $WORKING_DIR/.env
	. $WORKING_DIR/.env
fi


echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER run --rm ${EXTRA_CONTAINER_OPTION} --name artemis -p 61616:61616 -p 8161:8161 apache/activemq-artemis:latest-alpine
