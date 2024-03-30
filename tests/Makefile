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
# password seed is needed on external tests for client/server sync
SEED    := $(shell head -c 33 /dev/urandom | base64)
# SEED    = "test-seed"

.PHONY: check.external
check.external:
	source $(VENV)/bin/activate
	export TEST_SEED="$(SEED)"
	export FLASK_TESTER_URL="http://localhost:$(PORT)"
	# app
	flask --app app run --port=$(PORT) &
	flask_pid=$$!
	sleep $(SLEEP)
	$(PYTEST) $(PYTOPT) test_app.py
	kill $$flask_pid
	# app2
	flask --app app2 run --port=$(PORT) &
	flask_pid=$$!
	sleep $(SLEEP)
	$(PYTEST) $(PYTOPT) test_app2.py
	kill $$flask_pid

.PHONY: check.internal
check.internal:
	source $(VENV)/bin/activate
	# app
	export FLASK_TESTER_APP="app"
	$(PYTEST) $(PYTOPT) test_app.py
	# app2
	export FLASK_TESTER_APP="app2:create_app"
	$(PYTEST) $(PYTOPT) test_app2.py

.PHONY: check.coverage
check.coverage:
	$(MAKE) PYTEST="coverage run -a -m $(PYTEST)" check.internal
	coverage html ../FlaskTester.py
	coverage report --show-missing --precision=1 --fail-under=100.0

.PHONY: check
check: check.internal check.external
