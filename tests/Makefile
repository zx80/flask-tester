SHELL   = /bin/bash
.ONESHELL:

VENV    = ../venv
PORT    = 5000
SLEEP   = 3

.PHONY: clean
clean:
	$(RM) -r __pycache__

FLASK   = flask
PYTEST  = pytest --log-level=debug --capture=tee-sys
PYTOPT  =

.PHONY: check.external
check.external:
	source $(VENV)/bin/activate
	flask run --port=$(PORT) &
	flask_pid=$$?
	sleep $(SLEEP)
	export FLASK_TESTER_URL="http://localhost:$(PORT)"
	$(PYTEST) $(PYTOPT) test.py
	kill $$flask_pid

.PHONY: check.internal
check.internal:
	source $(VENV)/bin/activate
	export FLASK_TESTER_APP=app
	pytest test.py 

.PHONY: check
check: check.internal check.external
