# How to start a graph database

There is a script named run_artemis.sh in the same directory of this document.
The script starts a artemis MQ broker in a container

Be sure to define POD_CONTAINER variable before running this script.

If a .env file is present, it will read the environment variables from there.
The .env file should be in the same directory as the script.

Rename the .env.example file to .env and set the environment variables.