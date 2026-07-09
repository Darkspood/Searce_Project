.PHONY: venv install install-dev run test test-verbose clean

VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
STREAMLIT := $(VENV)/bin/streamlit
PYTEST := $(VENV)/bin/pytest

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -r requirements.txt

install-dev: venv
	$(PIP) install -r requirements-dev.txt

run:
	$(STREAMLIT) run app.py

test:
	$(PYTEST)

test-verbose:
	$(PYTEST) -v

clean:
	rm -rf $(VENV) .pytest_cache **/__pycache__
