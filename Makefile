.SILENT:
SHELL := /bin/bash

# Some defs
REQS := requirements.txt
VENV := venv
IN_VENV := source $(VENV)/bin/activate &&
SRC := src
OUT := out
FLAKE_REPORT := $(OUT)/flake-report/index.html
PYTHON_FILES := $(shell find $(SRC) -name '*.py')
#GIT_VERSION := $(shell git describe --tags 2>/dev/null || true)
GIT_VERSION := 0.0.0
VERSION := $(shell echo "$(GIT_VERSION)" | sed -e "s/\(.*\)-\([0-9]*\)-\(.*\)/\1.post\2+\3/")
ARTIFACTS := $(OUT)/artifacts
PYTHON_DIST := $(ARTIFACTS)/nmk-$(VERSION).tar.gz

# Default target
.PHONY: default
default: build

# Clean
.PHONY: clean
clean:
	git clean -fdX

# Venv build
$(VENV): $(REQS)
	python3 -m venv $(VENV)
	$(IN_VENV) pip install pip --upgrade
	$(IN_VENV) pip install -r $(REQS)

# Venv clean
.PHONY: clean-venv
clean-venv:
	rm -Rf $(VENV)

# Black
.PHONY: black
black:
	$(IN_VENV) black -l 160 $(SRC)

# Isort
.PHONY: isort
isort:
	$(IN_VENV) isort $(SRC)

# Flake8
$(FLAKE_REPORT): $(PYTHON_FILES)
	rm -Rf `dirname $(FLAKE_REPORT)`
	mkdir -p `dirname $(FLAKE_REPORT)`
	$(IN_VENV) flake8 $(SRC)

# Build
.PHONY: build
build: $(PYTHON_DIST)
$(PYTHON_DIST): $(PYTHON_FILES) $(VENV) black isort $(FLAKE_REPORT)
	$(IN_VENV) python setup.py sdist --dist-dir $(ARTIFACTS)
