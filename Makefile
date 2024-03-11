# convenient makefile

SHELL	= /bin/bash
.ONESHELL:

MODULE	= FlaskTester

F.md	= $(wildcard *.md)
F.pdf	= $(F.md:%.md=%.pdf)

# PYTHON	= /snap/bin/pypy3
# PYTHON	= python3
PYTHON	= python
PIP		= venv/bin/pip

.PHONY: check check.mypy check.ruff check.pytest check.demo check.coverage check.docs
check.mypy: venv
	source venv/bin/activate
	mypy --implicit-optional --check-untyped-defs $(MODULE).py

check.pyright: venv
	source venv/bin/activate
	pyright $(MODULE).py

# E127,W504
check.ruff: venv
	source venv/bin/activate
	ruff check --ignore=E227,E402,E501,E721,F401,F811 $(MODULE).py

check.pytest: venv
	source venv/bin/activate
	$(MAKE) -C tests check

check.coverage: venv
	source venv/bin/activate
	$(MAKE) -C tests check.coverage

# MD013: line length
check.docs:
	source venv/bin/activate
	pymarkdown -d MD013 scan *.md
	# sphinx-lint docs/

check: venv
	source venv/bin/activate
	type $(PYTHON)
	$(MAKE) check.mypy
	$(MAKE) check.pyright
	$(MAKE) check.docs
	$(MAKE) check.ruff
	$(MAKE) check.pytest && \
	$(MAKE) check.coverage

.PHONY: clean clean.venv
clean:
	$(RM) -r __pycache__ */__pycache__ dist build .mypy_cache .pytest_cache
	$(RM) $(F.pdf)
	$(MAKE) -C tests clean

clean.venv: clean
	$(RM) -r venv *.egg-info

# for local testing
venv:
	$(PYTHON) -m venv venv
	$(PIP) install -U pip
	$(PIP) install -e .[dev,doc]

$(MODULE).egg-info: venv
	$(PIP) install -e .

# generate source and built distribution
dist: venv
	source venv/bin/activate
	$(PYTHON) -m build

.PHONY: publish
publish: dist
	# provide pypi login/pw or token somewhere…
	echo venv/bin/twine upload dist/*

# generate pdf doc
MD2PDF  = pandoc -f markdown -t latex -V papersize:a4 -V geometry:hmargin=2.5cm -V geometry:vmargin=3cm

%.pdf: %.md
	$(MD2PDF) -o $@ $<
