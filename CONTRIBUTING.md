Contributing to wise-agents
==================================

Welcome to the wise-agents project! We welcome contributions from the community. This guide will walk you through the steps for getting started on our project.

- [Forking the Project](#forking-the-project)
- [Issues](#issues)
  - [Good First Issues](#good-first-issues)
- [Setting up your Developer Environment](#setting-up-your-developer-environment)
- [Contributing Guidelines](#contributing-guidelines)
- [Community](#community)


## Forking the Project 
To contribute, you will first need to fork the [wise-agents](https://github.com/wise-agents/wise-agents) repository. 

This can be done by looking in the top-right corner of the repository page and clicking "Fork".
![fork](/images/fork.jpg)

The next step is to clone your newly forked repository onto your local workspace. This can be done by going to your newly forked repository, which should be at `https://github.com/USERNAME/wise-agents`. 

Then, there will be a green button that says "Code". Click on that and copy the URL.



Then, in your terminal, paste the following command:
```bash
git clone [URL]
```
Be sure to replace [URL] with the URL that you copied.

Now you have the repository on your computer!

## Issues
The wise-agents project uses GitHub to manage issues. All issues can be found [here](https://github.com/wise-agents/wise-agents/issues). 

To create a new issue, comment on an existing issue, or assign an issue to yourself, you'll need to first [create a GitHub account](https://github.com/).


### Good First Issues
Want to contribute to the wise-agents project but aren't quite sure where to start? Check out our issues with the `good-first-issue` label. These are a triaged set of issues that are great for getting started on our project. These can be found [here](https://github.com/wise-agents/wise-agents/labels/good%20first%20issue). 

Once you have selected an issue you'd like to work on, make sure it's not already assigned to someone else, and assign it to yourself.

It is recommended that you use a separate branch for every issue you work on. To keep things straightforward and memorable, you can name each branch using the GitHub issue number. This way, you can have multiple PRs open for different issues. For example, if you were working on [issue-125](https://github.com/wise-agents/wise-agents/issues/125), you could use issue-125 as your branch name.

## Setting up your Developer Environment
You will need:

* Python 3.12+
* Git
* An [IDE](https://en.wikipedia.org/wiki/Comparison_of_integrated_development_environments#Python)
(e.g., [Microsoft Visual Studio Code](https://code.visualstudio.com/))

To setup your development environment you need to:

1. First `cd` to the directory where you cloned the project (eg: `cd wise-agents`)

2. Create a Python virtual environment for the project.

    The venv module supports creating lightweight “virtual  environments”, each with their own independent set of Python packages installed in their site directories. A virtual environment is created on top of an existing Python installation, known as the virtual environment’s “base” Python, and may optionally be isolated from the packages in the base environment, so only those explicitly installed in the virtual environment are available.
For more information about virtual environment see [here](https://docs.python.org/3/library/venv.html)

    ```
    python -m venv .venv
    ```

    OR just using our Makefile

    ```
    make venv
    ```

3. Activate the venv
    
    ```
    source .venv/bin/activate
    ```
    
    OR just using our Makefile
    
    ```
    make activate_venv
    ```

4. Add a remote ref to upstream, for pulling future updates.
For example:

    ```
    git remote add upstream https://github.com/wise-agents/wise-agents
    ```

5. To build `wise-agents` run:
    
    ```
    make install
    ```

6. To run the tests:
    * start artemis: set .env for artemis see [artemis/README.MD](artemis/). Then start it using
        
        ```
        make artemis
        ```

    * start graphdb: set .env for graphdb see [graphdb/README.MD](graphdb/). Then start it using
        
        ```
        make graphdb
        ```

    * start vectordb: set .env for vectordb see [vectordb/README.MD](vectordb/). Then start it using
        
        ```
        make vectordb
        ```

    * start LLM model serving: set .env for model-serving see [model-serving/README.MD](model-serving/). Then start it using
        
        ```
        make model
        ```

    * run the tests:
        
        ```
        make test
        ```


7. To run only a specific test, use:
    * If you want to run a single test you can specify the test with -k option: ``pytest -k test_register_agents --log-cli-level=DEBUG``
    * You can also run all tests contained in a single file with the same option ``pytest -k test_WiseAgentRegistry --log-cli-level=DEBUG``
    * Note the name of the file could be partial so for example ``pytest -k test_yaml --log-cli-level=DEBUG`` will run test contained in ``tests/wiseagents/test_yaml_deserializer.py`` and ``tests/wiseagents/test_yaml_serialization.py)



## Contributing Guidelines

When submitting a PR, please keep the following guidelines in mind:

1. In general, it's good practice to squash all of your commits into a single commit. For larger changes, it's ok to have multiple meaningful commits. If you need help with squashing your commits, feel free to ask us how to do this on your pull request. We're more than happy to help!

2. Please link the issue you worked on in the description of your pull request and in your commit message. For example, for issue-125, the PR description and commit message could be: ```Go through TODOs in the code and create issues for them  
Fixes #125```

3. Your PR should include [docstrings](https://google.github.io/styleguide/pyguide.html) for all functions and classes, as well as comments to help make your code easier to understand.

4. Your PR should include [tests](https://github.com/wise-agents/wise-agents/tree/main/tests) for the functionality that you are adding.

5. Your PR should include appropriate [documentation](https://github.com/wise-agents/wise-agents/tree/main/docs) for the functionality that you are adding. This could involve updating an existing section in the documentation or adding a new page in the documentation.

6. Your PR should include an [example](https://github.com/wise-agents/wise-agents/tree/main/examples) of how to use the new functionality that you are adding.

> [!NOTE]
> There might be times where the documentation or example you need to add is a bit more involved. For cases like this, if
the functionality you are adding is needed urgently (e.g., to allow someone else to work on a feature that depends on yours),
you can create an issue to track the documentation or example to be added and make sure to reference this issue in your PR.
This way, we can merge your PR while still ensuring that the documentation or example is added soon after.


## Code Reviews

All submissions, including submissions by project members, need to be reviewed by at least one wise-agents committer before being merged.

The [GitHub Pull Request Review Process](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews) is followed for every pull request.


## Community
For more information on how to get involved with Wise Agents, check out our [community](https://wise-agents.github.io/community/) page.