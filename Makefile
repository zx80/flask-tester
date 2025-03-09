# convenient makefile

SHELL	= /bin/bash
.ONESHELL:

MODULE	= FlaskTester

F.md	= $(wildcard *.md)
F.pdf	= $(F.md:%.md=%.pdf)

# PYTHON	= /snap/bin/pypy3
# PYTHON	= python3
PYTHON	= python

.PHONY: check.mypy
check.mypy: venv
	source venv/bin/activate
	mypy --implicit-optional --check-untyped-defs $(MODULE).py

.PHONY: check.pyright
check.pyright: venv
	source venv/bin/activate
	pyright $(MODULE).py

# E127,W504
.PHONY: check.ruff
check.ruff: venv
	source venv/bin/activate
	ruff check --ignore=E227,E402,E501,E721,F401,F811 $(MODULE).py

.PHONY: check.pytest
check.pytest: venv
	source venv/bin/activate
	$(MAKE) -C tests check

.PHONY: check.coverage
check.coverage: venv
	source venv/bin/activate
	$(MAKE) -C tests check.coverage

# MD013: line length
.PHONY: check.docs
check.docs:
	source venv/bin/activate
	pymarkdown -d MD013 scan *.md
	sphinx-lint docs/

.PHONY: check
check: venv
	source venv/bin/activate
	type $(PYTHON)
	$(MAKE) check.mypy
	$(MAKE) check.pyright
	$(MAKE) check.docs
	$(MAKE) check.ruff
	$(MAKE) check.pytest && \
	$(MAKE) check.coverage

.PHONY: docs
docs: venv
	source venv/bin/activate
	$(MAKE) -C docs html
	find docs/_build -type d -print0 | xargs -0 chmod a+rx
	find docs/_build -type f -print0 | xargs -0 chmod a+r
	ln -s docs/_build/html _site

.PHONY: clean
clean:
	$(RM) -r __pycache__ */__pycache__ dist build .mypy_cache .pytest_cache .ruff_cache _site
	$(RM) $(F.pdf)
	$(MAKE) -C tests clean
	$(MAKE) -C docs clean

.PHONY: clean.venv
clean.venv: clean
	$(RM) -r venv *.egg-info

.PHONY: clean.dev
clean.dev: clean.venv

.PHONY: dev
dev: venv

.PHONY: venv.update
venv.update:
	source venv/bin/activate
	pip install -U pip
	pip install -e .[dev,doc]

# for local testing
venv:
	$(PYTHON) -m venv venv
	$(MAKE) venv.update

$(MODULE).egg-info: venv
	source venv/bin/activate
	pip install -e .

.PHONY: pub
pub: venv/.pub

venv/.pub: venv
	source venv/bin/activate
	pip install -e .[pub]
	touch $@

# generate source and built distribution
dist: pub
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
