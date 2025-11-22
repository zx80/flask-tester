# FlaskTester Versions

Packages are distributed from [PyPI](https://pypi.org/project/FlaskTester/),
[sources](https://github.com/zx80/flask-tester) are available on GitHub,
see also the [documentation](https://zx80.github.io/flask-tester/),
please report any [issues](https://github.com/zx80/flask-tester/issues).

## TODO

- setPass and fake auth?
- fixture scope?
- document file upload tests?
- activate _Pypy 3.11_ and _Python 3.14_ in GitHub CI.
- mkdocs? docsify?

## 5.1 on 2025-11-22

- use SPDX licensing format.
- minor test and CI configuration cleanup and extensions.
- this version description cleanup.

## 5.0 on 2025-03-09

- add `setHook`.
- slightly improve documentation.
- add some tests.
- improve `Makefile`.

## 4.3 on 2024-08-10

- improve comments.
- activate _Python 3.13_ and _Pypy 3.10_ in GitHub CI.
- restrict CI to _main_ branch.
- add explicit `bcrypt` dependency for tests.
- allow mixing `json` and `data` parameters by merging into `data`.

## 4.2 on 2024-07-28

- fix bug about string parameters introduced in 4.1.

## 4.1 on 2024-07-28

- add support for transparent dataclass and pydantic parameters.

## 4.0 on 2024-05-20

- improved documentation and tests.
- remove deprecated `FLASK_TESTER_URL`, simplifying code in passing.
- remove deprecated `check` method.

## 3.6 on 2024-03-30

- only use `FLASK_TESTER_APP`, hide `FLASK_TESTER_URL`, which is only kept for
  upward compatibility and is deprecated.
- improved documentation, including a working `app2`.

## 3.5 on 2024-03-30

- improve failure behavior and testing.

## 3.4 on 2024-03-30

- add `ptype` to control the default parameter type.
- mark `check` as deprecated.
- make method-specific check methods handle positional status and content.
- improved intro example.
- split documentation in several pages.
- improve API documentation.
- use FSA 30 for testing.

## 3.3 on 2024-03-25

- fix missing parameter on `check` to ensure upward compatibility.

## 3.2 on 2024-03-24

- improved documentation.
- simpler code and API documentation.

## 3.1 on 2024-03-24

- more consistent test and demo code.
- reach actual full coverage, without _any_ pragma.
- fix default allowed authenticator schemes.

## 3.0 on 2024-03-23

- add support for `none` authentication, with only cookies.

## 2.0 on 2024-03-23

- add support for cookies.
- improved documentation and code.
- improved tests.

## 1.4 on 2024-03-19

- test expected assert failures.
- improved API documentation.
- keep first found app.

## 1.3 on 2024-03-16

- generate API documentation.
- cleaner code.

## 1.2 on 2024-03-15

- improved documentation and tests.
- raise an error when setting unusable passwords or tokens.
- add support for `pkg:name` application syntax.
- use random passwords when testing.

## 1.1 on 2024-03-13

- improve coverage tests.
- add `FLASK_TESTER_LOG_LEVEL` environment to set the log level.
- add explicit license section and file.
- add more links about the project.

## 1.0 on 2024-03-12

- add `FLASK_TESTER_DEFAULT` environment configuration to `ft_client`.
- add `FLASK_TESTER_*` environment configurations to `ft_authenticator`.
- improve documentation, including incredible badges.
- working coverage tests.

## 0.9 on 2024-03-11

- initial revision extracted from a separate project.
