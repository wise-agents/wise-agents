# How to start a graph database

There is a script named run_graphdb.sh in the same directory of this document.
The script starts a graph database.

It reads the username, password, and database name to be used to connect to the graph database
from the environment variables. Be sure to define these variables before running this script.

```   
    export NEO4J_USERNAME=USERNAME_TO_CONNECT_TO_NEO4J
    export NEO4J_PASSWORD=PASSWORD_TO_CONNECT_TO_NEO4J
    export NEO4J_DATABASE=DATABASE_NAME_TO_CONNECT_TO
    export POD_CONTAINER=podman | docker
```

As an example, the above variables could be set to:

```   
    export NEO4J_USERNAME=neo4j
    export NEO4J_PASSWORD=neo4jpassword
    export NEO4J_DATABASE=neo4j
    export POD_CONTAINER=docker
```

If a .env file is present, it will read the environment variables from there.
The .env file should be in the same directory as the script.

Rename the .env.example file to .env and set the environment variables.