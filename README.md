# FlaskTester - Pytest fixtures for Flask internal and external tests

This package allows to run authenticated tests against a Flask application,
either with internal Flask tests (aka `test_client`) or external tests (with
`requests` which performs actual HTTP requests).

Only one set of tests is needed, switching from internal to external is
achieved through environment variables.

![Status](https://github.com/zx80/flask-tester/actions/workflows/package.yml/badge.svg?branch=master&style=flat)
![Tests](https://img.shields.io/badge/tests-2%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-0%25-success)
![Issues](https://img.shields.io/github/issues/zx80/flask-tester?style=flat)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/FlaskTester)
![Badges](https://img.shields.io/badge/badges-8-informational)
![License](https://img.shields.io/pypi/l/flasktester?style=flat)

## Fixtures

The package provides two fixtures:

- `ft_authenticator` for app authentication, which depends on two environment variables:

  - `FLASK_TESTER_ALLOW` space-separated list of allowed authentication schemes.
  - `FLASK_TESTER_AUTH` comma-separated list of _login:password_ credentials.

- `ft_client` for app testing, which depends on the previous fixture, plus environment
  variables which allow to find the application, at least one must be defined.

  - `FLASK_TESTER_DEFAULT` default login for authentication.
  - `FLASK_TESTER_URL` URL of the running application for external tests.
  - `FLASK_TESTER_APP` package (filename with `.py`) to be imported for the application.
    - the application is expected to be named `app`
    - if not available, look and call for `create_app`

  The authenticator is available as `_auth` in the client fixture.

```python
import os
import pytest
from FlaskTester import ft_authenticator, ft_client

@pytest.fixture
def api(ft_client):
    # get Calvin's token, assume {"token": "<token-value>"}
    res = ft_client.get("/token", login="calvin", auth="basic", status=200)
    assert res.is_json
    ft_client._auth.setToken("calvin", res.json["token"])
    yield ft_client

def test_app(api):
    api.get("/admin", login="calvin", auth="bearer", status=200)
    api.get("/admin", login="calvin", auth="basic", status=200)
    api.get("/admin", login="hobbes", auth="basic", status=401)
```

Authenticator environment variables can be set from the pytest Python test file by
assigning them through `os.environ`.

## Classes

The implementation of these fixtures is based on five classes:

- `Authenticator` class to store test credentials.

  Use `setPass` and `setToken` to add user credentials.

- `RequestFlaskResponse` class to turn a `requests` response into
  a Flask-looking response, with the following attributes: `status_code`,
  `data`, `text`, `headers`, `cookies`, `is_json` and `json`.

- `Client` abstract class to run test, with two implementations.

  The class provides usual `get`, `post`… per-HTTP-method methods,
  and a more generic `request` method.

  These methods expect the following named parameters:

  - `login` for user login to use for authentication.
  - `auth` for the authentication scheme to use for this request,
    otherwise allowed schemes are tried, with tokens first.
  - `status` for the expected HTTP status code.

  For the check methods, the mandatory parameters are the method, the path
  and the expected status.

- `FlaskClient` implementation class for internal tests.

   This class is mostly the standard `test_client` with the above parameters
   extensions.

- `RequestClient` implementation class for external (real HTTP) tests.

  The path is relative to the URL provided to the constructor.

## TODO

- API documentation generation
- coverage tests

## Versions

### 0.10 on ?

Add `FLASK_TESTER_DEFAULT` environment configuration to `ft_client`.
Improve documentation, including incredible badges.

### 0.9 on 2024-03-11

Initial revision extracted from a separate project.
