# FlaskTester - Pytest fixtures for Flask internal and external authenticated tests

This package allows to run authenticated tests against a Flask application,
either with internal Flask tests (aka `test_client`) or external tests (with
`requests` which performs actual HTTP requests), including password and token
authentication.

Only one set of tests is needed, switching from internal to external is
achieved through environment variables.

![Status](https://github.com/zx80/flask-tester/actions/workflows/package.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-10%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Issues](https://img.shields.io/github/issues/zx80/flask-tester?style=flat)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/FlaskTester)
![Badges](https://img.shields.io/badge/badges-8-informational)
![License](https://img.shields.io/pypi/l/flasktester?style=flat)

## Usage

Install package with `pip install FlaskTester` or equivalent.

The following test creates a local fixture with 2 users identified by a
password, and retrieves a token for the first user using a `/token` route
provided by the application.
It then proceeds to run some requests against the `/admin` route.

```python
import secret
import pytest
from FlaskTester import ft_authenticator, ft_client

@pytest.fixture
def app(ft_client):
    # add test passwords for Calvin and Hobbes (must be consistent with app!)
    ft_client.setPass("calvin", secret.PASSES["calvin"])
    ft_client.setPass("hobbes", secret.PASSES["hobbes"])
    # get Calvin's token, assume json result {"token": "<token-value>"}
    res = ft_client.get("/token", login="calvin", auth="basic", status=200)
    assert res.is_json
    ft_client.setToken("calvin", res.json["token"])
    # return working client
    yield ft_client

def test_app(app):
    app.get("/admin", login="calvin", auth="bearer", status=200)
    app.get("/admin", login="calvin", auth="basic", status=200)
    res = app.get("/admin", login="hobbes", auth="basic", status=403)
    assert 'not in group "ADMIN"' in res.text
```

This can be run against a (local) server:

```shell
flask --app app:app run &                        # start flask app
pid=$!                                           # keep pid
export FLASK_TESTER_URL="http://localhost:5000"  # set app local url
pytest test.py                                   # run external tests
kill $pid                                        # stop app with pid
```

Or locally with the Flask internal test infrastructure:

```shell
export FLASK_TESTER_APP="app:app"                # set app module
pytest test.py                                   # run internal tests
```

The above test runs with [`tests/app.py`](tests/app.py)
[Flask](https://flask.palletsprojects.com/)
REST application back-end with password and token authentication based on
[FlaskSimpleAuth](https://pypi.org/project/FlaskSimpleAuth/).

## Fixtures

The package provides two fixtures:

- `ft_authenticator` for app authentication, which depends on environment variables:

  - `FLASK_TESTER_ALLOW` space-separated list of allowed authentication schemes,
    default is `["bearer", "basic", "param"]`.
  - `FLASK_TESTER_AUTH` comma-separated list of _login:password_ credentials.
  - `FLASK_TESTER_USER` user login parameter for `param` password authentication,
    default is `USER`.
  - `FLASK_TESTER_PASS` user password parameter for `param` password authentication,
    default is `PASS`.
  - `FLASK_TESTER_LOGIN` user login parameter for `fake` authentication,
    default is `LOGIN`.
  - `FLASK_TESTER_TPARAM` token parameter for `tparam` token authentication,
    default is `AUTH`.
  - `FLASK_TESTER_BEARER` bearer scheme for `bearer` token authentication,
    default is `Bearer`.
  - `FLASK_TESTER_HEADER` header name for for `header` token authentication,
    default is `Auth`.
  - `FLASK_TESTER_COOKIE` cookie name for for `cookie` token authentication,
    default is `auth`.
  - `FLASK_TESTER_LOG_LEVEL` log level for module,
    default is `NOTSET`.

  The fixture has 3 main methods:
  - `setPass` to associate a password to a user, set to _None_ to remove credential.
  - `setToken` to associate a token to a user, set to _None_ to remove credential.
  - `setAuth` to add authentication data to a request `kwargs`.

- `ft_client` for app testing, which depends on the previous fixture, plus
  environment variables which allow to find the application, at least one must
  be defined:

  - `FLASK_TESTER_URL` URL of the running application for external tests.
    The application is expected to be already running when the test is started.

  - `FLASK_TESTER_APP` package (filename with `.py`) to be imported for the application.
    - for `pkg:name`, `name` is the application in `pkg`.
    - for `pkg`, look for app as `app`, `application`, `create_app`, `make_app`.
    - in both cases, `name` is called if callable and not a Flask application.

  Moreover:
  - `FLASK_TESTER_DEFAULT` default login for authentication, default is _None_.

  The fixture then provides test methods to issue test requests against a Flask application:
  - `request` generic request with `login`, `auth`, `status` end `content` extensions.
  - `get post put patch delete` methods with `login`, `auth` and `status` extensions.
  Moreover, `setPass` and `setToken` are forwarded to the internal authenticator.

Authenticator environment variables can be set from the pytest Python test file by
assigning them through `os.environ`.

## Classes

The implementation of these fixtures is based on five classes plus exceptions:

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

  File parameters in `data`, with the format expected by the Flask test client,
  are turned into `files` parameters as expected by `requests`.

- The following exceptions are defined:
  - `FlaskTesterError` root class for exceptions.
  - `AuthError` authentication-related errors.

## License

This code is public domain.

Packages are distributed from [PyPI](https://pypi.org/project/FlaskTester/),
[sources](https://github.com/zx80/flask-tester) are available on GitHub,
see also the [documentation](https://zx80.github.io/flask-tester/),
please report any [issues](https://github.com/zx80/flask-tester/issues).

## See Also, or Not

- [Flask Testing](https://github.com/jarus/flask-testing) an unmaintained
  old-style unit test for Flask 1.x, without authentication help.

## TODO

- API documentation generation

## Versions

### 1.2 on 2024-03-15

Improved documentation and tests.
Raise an error when setting unusable passwords or tokens.
Add support for `pkg:name` application syntax.
Use random passwords when testing.

### 1.1 on 2024-03-13

Improve coverage tests.
Add `FLASK_TESTER_LOG_LEVEL` environment to set the log level.
Add explicit license section and file.
Add more links about the project.

### 1.0 on 2024-03-12

Add `FLASK_TESTER_DEFAULT` environment configuration to `ft_client`.
Add `FLASK_TESTER_*` environment configurations to `ft_authenticator`.
Improve documentation, including incredible badges.
Working coverage tests.

### 0.9 on 2024-03-11

Initial revision extracted from a separate project.
