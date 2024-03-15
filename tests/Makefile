SHELL   = /bin/bash
.ONESHELL:

VENV    = ../venv
SLEEP   = 3

.PHONY: clean
clean:
	$(RM) -r __pycache__ htmlcov
	$(RM) .coverage

FLASK   = flask
PORT    = 5000
PYTEST  = pytest --log-level=debug --capture=tee-sys
PYTOPT  =
SEED    = $(shell head -c 33 /dev/urandom | base64)

.PHONY: check.external
check.external:
	source $(VENV)/bin/activate
	export TEST_SEED="$(SEED)"
	flask --app app:app run --port=$(PORT) &
	flask_pid=$$!
	sleep $(SLEEP)
	export FLASK_TESTER_URL="http://localhost:$(PORT)"
	$(PYTEST) $(PYTOPT) test.py
	kill $$flask_pid

.PHONY: check.internal
check.internal:
	source $(VENV)/bin/activate
	export TEST_SEED="$(SEED)"
	export FLASK_TESTER_APP="app:create_app"
	$(PYTEST) $(PYTOPT) test.py

.PHONY: check.coverage
check.coverage:
	$(MAKE) PYTEST="coverage run -m $(PYTEST)" check.internal
	coverage html ../FlaskTester.py
	coverage report --show-missing --precision=1 --fail-under=100.0

.PHONY: check
check: check.internal check.external
