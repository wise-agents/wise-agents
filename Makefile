# system python interpreter. used only to create virtual environment
PY = python3
VENV = .venv
BIN=$(VENV)/bin

# make it work on windows too
ifeq ($(OS), Windows_NT)
    BIN=$(VENV)/Scripts
    PY=python
endif

.PHONY: venv clean install test artemis graphdb model

## help: Show help
help: Makefile
	@printf "\n\033[1mUsage: make <TARGETS> ...\033[0m\n\n\033[1mTargets:\033[0m\n\n"
	@sed -n 's/^## //p' $< | awk -F':' '{printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort | sed -e 's/^/  /'

## venv: Create virtual environment
$(VENV):
	$(PY) -m venv $(VENV)

## clean: Cleans the generated files
clean:
	rm -Rf $(VENV)

## install: Runs pip install
install:
	pip install -e .

#lint: $(VENV)
#	$(BIN)/flake8

## all: Runs the tests
all: test

## test: Run the tests
test: $(VENV)
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
