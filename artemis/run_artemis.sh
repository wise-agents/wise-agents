#!/bin/bash
# This script is used to run the artemis MQ broker in a container

# define these variables before running the script
#export POD_CONTAINER = podman | docker

# If a .env file is present, it will read the environment variables from there
# The .env file should be in the same directory as the script
# Rename the .env.example file to .env and set the environment variables
if [ -f ./.env ]; then
	. ./.env
fi

echo "Pod container: $POD_CONTAINER"

$POD_CONTAINER run --rm --name mycontainer -p 61616:61616 -p 8161:8161 --rm apache/activemq-artemis:latest-alpine
