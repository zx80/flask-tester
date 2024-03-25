# FlaskTester - Pytest fixtures for Flask internal and external authenticated tests

This package allows to run authenticated tests against a Flask application,
either with internal Flask tests (aka `test_client`) or external tests (with
`requests` which performs actual HTTP requests), including password and token
authentication and per-user cookies.

Only one set of tests is needed, switching from internal to external is
achieved through environment variables.

![Status](https://github.com/zx80/flask-tester/actions/workflows/package.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-12%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Issues](https://img.shields.io/github/issues/zx80/flask-tester?style=flat)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/FlaskTester)
![Badges](https://img.shields.io/badge/badges-8-informational)
![License](https://img.shields.io/pypi/l/flasktester?style=flat)

## Usage

Install package with `pip install FlaskTester` or equivalent.

The following test creates a local fixture with 2 users identified by a
password, and retrieves tokens for both users using a `/login` route
provided by the application.
It then proceeds to run authenticated requests against the `/admin` route.

```python
import pytest
from FlaskTester import ft_authenticator, ft_client
import secret

@pytest.fixture
def app(ft_client):
    # add test passwords for Calvin and Hobbes (must be consistent with app!)
    ft_client.setPass("calvin", secret.PASSES["calvin"])
    ft_client.setPass("hobbes", secret.PASSES["hobbes"])
    # get user tokens, assume json result {"token": "<token-value>"}
    res = ft_client.get("/login", login="calvin", auth="basic", status=200)
    assert res.is_json
    ft_client.setToken("calvin", res.json["token"])
    res = ft_client.post("/login", login="hobbes", auth="param", status=201)
    assert res.is_json
    ft_client.setToken("hobbes", res.json["token"])
    # also set a cookie
    ft_client.setCookie("hobbes", "lang", "fr")
    ft_client.setCookie("calvin", "lang", "en")
    # return working client
    yield ft_client

def test_app_admin(app):
    # try all authentication schemes for calvin
    app.get("/admin", login="calvin", auth="bearer", status=200)
    app.get("/admin", login="calvin", auth="basic", status=200)
    app.get("/admin", login="calvin", auth="param", status=200)
    # try all authentication schemes for hobbes
    res = app.get("/admin", login="hobbes", auth="bearer", status=403)
    assert 'not in group "ADMIN"' in res.text
    res = app.get("/admin", login="hobbes", auth="basic", status=403)
    assert 'not in group "ADMIN"' in res.text
    res = app.get("/admin", login="hobbes", auth="param", status=403)
    assert 'not in group "ADMIN"' in res.text
```

This can be run against a (local) server:

```shell
export TEST_SEED="some-random-data"              # shared test seed
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
The code uses _25_ lines of Python for implementing
password (basic and parameters) and token authentications,
admin group authorization, and routes for
token generation (2), identity tests (2) and an incredible open cookie-based
translation service.

## Fixtures

The package provides two fixtures:

- `ft_authenticator` for app authentication, which depends on environment variables:

  - `FLASK_TESTER_ALLOW` space-separated list of allowed authentication schemes,
    default is `["bearer", "basic", "param", "none"]`.
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

  The fixture has 4 main methods:
  - `setPass` to associate a password to a user, set to _None_ to remove credential.
  - `setToken` to associate a token to a user, set to _None_ to remove credential.
  - `setCookie` to add a cookie to a user, set value to _None_ to remove cookie.
  - `setAuth` to add authentication data to a request `kwargs` and `cookies`.  
    This method is called automatically for adding credentials to a request.

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
  Moreover, `setPass`, `setToken` and `setCookie` are forwarded to the internal authenticator.

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

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence… Beware that you may lose your
hairs or your friends because of it. If you like it, feel free to send a
postcard to the author.

## Versions

Packages are distributed from [PyPI](https://pypi.org/project/FlaskTester/),
[sources](https://github.com/zx80/flask-tester) are available on GitHub,
see also the [documentation](https://zx80.github.io/flask-tester/),
please report any [issues](https://github.com/zx80/flask-tester/issues).

### 3.3 on 2024-03-25

Fix missing parameter on `check` to ensure upward compatibility.

### 3.2 on 2024-03-24

Improved documentation.
Simpler code and API documentation.

### 3.1 on 2024-03-24

More consistent test and demo code.
Reach actual full coverage, without _any_ pragma.
Fix default allowed authenticator schemes.

### 3.0 on 2024-03-23

Add support for `none` authentication, with only cookies.

### 2.0 on 2024-03-23

Add support for cookies.
Improved documentation and code.
Improved tests.

### 1.4 on 2024-03-19

Test expected assert failures.
Improved API documentation.
Keep first found app.

### 1.3 on 2024-03-16

Generate API documentation.
Cleaner code.

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

## See Also, or Not

- [Flask Testing](https://github.com/jarus/flask-testing) an unmaintained
  old-style unit test for Flask 1.x, without authentication help.
