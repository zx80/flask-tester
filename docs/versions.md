# FlaskTester Versions

Packages are distributed from [PyPI](https://pypi.org/project/FlaskTester/),
[sources](https://github.com/zx80/flask-tester) are available on GitHub,
see also the [documentation](https://zx80.github.io/flask-tester/),
please report any [issues](https://github.com/zx80/flask-tester/issues).

## TODO

Check whether data and json should be exclusive.

## 4.3 on 2024-08-10

Improve comments.
Activate _Python 3.13_ and _Pypy 3.10_ in GitHub CI.
Restrict CI to _main_ branch.
Add explicit `bcrypt` dependency for tests.
Allow mixing `json` and `data` parameters by merging into `data`.

## 4.2 on 2024-07-28

Fix bug about string parameters introduced in 4.1.

## 4.1 on 2024-07-28

Add support for transparent dataclass and pydantic parameters.

## 4.0 on 2024-05-20

Improved documentation and tests.
Remove deprecated `FLASK_TESTER_URL`, simplifying code in passing.
Remove deprecated `check` method.

## 3.6 on 2024-03-30

Only use `FLASK_TESTER_APP`, hide `FLASK_TESTER_URL`, which is only kept for
upward compatibility and is deprecated.
Improved documentation, including a working `app2`.

## 3.5 on 2024-03-30

Improve failure behavior and testing.

## 3.4 on 2024-03-30

Add `ptype` to control the default parameter type.
Mark `check` as deprecated.
Make method-specific check methods handle positional status and content.
Improved intro example.
Split documentation in several pages.
Improve API documentation.
Use FSA 30 for testing.

## 3.3 on 2024-03-25

Fix missing parameter on `check` to ensure upward compatibility.

## 3.2 on 2024-03-24

Improved documentation.
Simpler code and API documentation.

## 3.1 on 2024-03-24

More consistent test and demo code.
Reach actual full coverage, without _any_ pragma.
Fix default allowed authenticator schemes.

## 3.0 on 2024-03-23

Add support for `none` authentication, with only cookies.

## 2.0 on 2024-03-23

Add support for cookies.
Improved documentation and code.
Improved tests.

## 1.4 on 2024-03-19

Test expected assert failures.
Improved API documentation.
Keep first found app.

## 1.3 on 2024-03-16

Generate API documentation.
Cleaner code.

## 1.2 on 2024-03-15

Improved documentation and tests.
Raise an error when setting unusable passwords or tokens.
Add support for `pkg:name` application syntax.
Use random passwords when testing.

## 1.1 on 2024-03-13

Improve coverage tests.
Add `FLASK_TESTER_LOG_LEVEL` environment to set the log level.
Add explicit license section and file.
Add more links about the project.

## 1.0 on 2024-03-12

Add `FLASK_TESTER_DEFAULT` environment configuration to `ft_client`.
Add `FLASK_TESTER_*` environment configurations to `ft_authenticator`.
Improve documentation, including incredible badges.
Working coverage tests.

## 0.9 on 2024-03-11

Initial revision extracted from a separate project.
