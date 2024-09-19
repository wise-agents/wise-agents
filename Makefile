# system python interpreter. used only to create virtual environment
PY = python3
VENV = .venv
BIN=$(VENV)/bin
ACTIVATE_VENV:= source $(VENV)/bin/activate

# make it work on windows too
ifeq ($(OS), Windows_NT)
    BIN=$(VENV)/Scripts
    ACTIVATE_VENV=$(VENV)\Scripts\activate
    PY=python
endif

.PHONY: help venv check_venv clean install test artemis graphdb vectordb model redis
.SILENT: check_venv

## help: Show help
help: Makefile
	@printf "\n\033[1mUsage: make <TARGETS> ...\033[0m\n\n\033[1mTargets:\033[0m\n\n"
	@sed -n 's/^## //p' $< | awk -F':' '{printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort | sed -e 's/^/  /'

## venv: Creates the virtual environment dir $(VENV)
venv: 
	$(PY) -m venv $(VENV)
	@echo "Created virtual environment directory $(VENV). Please, activate it by running '$(ACTIVATE_VENV)' in this terminal"

# fail_venv: Internal command isued to request for virtual environment activation
fail_venv:
	$(error Waiting on $(VENV) activation)

## check_venv: returns an error if virtual environment is not activated
check_venv:
ifeq ("$(wildcard $(VENV))", "")
	@echo "The virtual environment directory $(VENV) needs to be created and activated before running other targets. Creating dir..." 
	make --silent venv
	make --silent fail_venv
else ifeq ($(strip $(VIRTUAL_ENV)),)
	$(error Error: the virtual python environment is not activated. Please, run '$(ACTIVATE_VENV)' on this terminal to activate it)
endif

## clean: Cleans the generated files
clean:
	rm -Rf $(VENV)

## install: Runs pip install
install: check_venv
	pip install -e .

#lint: $(VENV)
#	$(BIN)/flake8

## all: Runs the tests
all: test

## test: Run the tests
test: check_venv
	pip install -e '.[test]'
	pytest

## artemis: Start artemis (this is a requirement to run the tests, see artemis/README.MD)
artemis:
	artemis/artemis.sh

## graphdb: Start GraphDB (this is a requirement to run the tests, see graphdb/README.MD)
graphdb:
	graphdb/run_graphdb.sh

## model: Serve model (this is a requirement to run the tests, see model-serving/README.MD)
model:
	model-serving/model_inference.sh

## vectordb: Start VectorDB (this is a requirement to run the tests, see vectordb/README.MD)
vectordb:
	vectordb/run_vectordb.sh

## redis: Start Redis (this is a requirement to run the tests, see redis/README.MD)
redis:
	redis/run_redis.sh
