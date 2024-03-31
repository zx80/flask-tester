# FlaskTester Documentation

This is the documentation for the fixtures and support classes provided
by `FlaskTester`.

## Fixtures

The package provides two fixtures:

- `ft_authenticator` for app authentication, which depends on environment variables:

  - `FLASK_TESTER_ALLOW` space-separated list of allowed authentication schemes,
    defaults to _bearer basic param none_.
  - `FLASK_TESTER_AUTH` comma-separated list of _login:password_ credentials,
    defaults to empty.
  - `FLASK_TESTER_USER` user login parameter for `param` password authentication,
    defaults to _USER_.
  - `FLASK_TESTER_PASS` user password parameter for `param` password authentication,
    defaults to _PASS_.
  - `FLASK_TESTER_LOGIN` user login parameter for `fake` authentication,
    defaults to _LOGIN_.
  - `FLASK_TESTER_TPARAM` token parameter for `tparam` token authentication,
    defaults to _AUTH_.
  - `FLASK_TESTER_BEARER` bearer scheme for `bearer` token authentication,
    defaults to _Bearer_.
  - `FLASK_TESTER_HEADER` header name for for `header` token authentication,
    defaults to _Auth_.
  - `FLASK_TESTER_COOKIE` cookie name for for `cookie` token authentication,
    defaults to _auth_.
  - `FLASK_TESTER_PTYPE` default type of parameters, `data` or `json`,
    defaults to _data_.
  - `FLASK_TESTER_LOG_LEVEL` log level for module,
    defaults to _NOTSET_.

  The fixture has 3 useful methods:

  - `setPass` to associate a password to a user, set to _None_ to remove credential.

    ```python
    auth.setPass("susie", "<susie-incredible-password>")
    ```

  - `setToken` to associate a token to a user, set to _None_ to remove credential.

    ```python
    auth.setToken("moe", "<moe's-token-computed-or-obtained-from-somewhere>")
    ```

  - `setCookie` to add a cookie to a user, set value to _None_ to remove cookie.

    ```python
    auth.setCookie("rosalyn", "lang", "en_US")
    ```

- `ft_client` for app testing, which depends on the previous fixture and
  is configured from two environment variables:

  - `FLASK_TESTER_APP` tells where to find the application, which may be the:

    - **URL** of the running application for external tests, eg _http://localhost:5000_.
      The application is expected to be already running when the test is started.

    - **Package** (filename without `.py`) to be imported for the application.
      - for _pkg:name_, _name_ is the application in _pkg_.
      - for _pkg_ only, look for app as _app_, _application_, _create_app_, _make_app_.
      - in both cases, _name_ is called if callable and not a Flask application.

    If not set, the defaults to _app_, which is to behave like Flask.

  - `FLASK_TESTER_DEFAULT` default login for authentication, defaults to _None_.

  The fixture then provides test methods to issue test requests against a Flask application:

  - `request` generic request with `login`, `auth`, `status` end `content` extensions.

    For instance, the following sumits a `POST` on path `/users` with one JSON parameter,
    as user _calvin_ using _basic_ authentication,
    expecting status code _201_ and some integer value (content regex) in the response body:

    ```python
    res = app.request("POST", "/users", 201, r"\d+", json={"username": "hobbes"},
                      login="calvin", auth="basic")
    assert res.is_json and "uid" in res.json
    uid = res.json["uid"]
    ```

    The authentication data, here a password, must have been provided to the authenticator.

  - `get post put patch delete` methods with the same extensions.

    Submit a `GET` request to path `/stats` authenticated as _hobbes_,
    expecting response status _200_:

    ```python
    app.get("/stats", 200, login="hobbes")
    ```

  Moreover, `setPass`, `setToken` and `setCookie` are forwarded to the internal authenticator.

Authenticator environment variables can be set from the pytest Python test file by
assigning them through `os.environ`.

The typical use case is to define a local fixture, set the authentication and
other data, and then proceed with it:

```python
import os
import pytest
from FlaskTester import ft_client, ft_authenticator
import secret

os.environ.update(FLASK_TESTER_ALLOW="basic param none")

@pytest.fixture
def app(ft_client):
    ft_client.setPass("calvin", secret.PASSES["calvin"])
    ft_client.setCookie("calvin", "lang", "en")
    ft_client.setPass("hobbes", secret.PASSES["hobbes"])
    ft_client.setCookie("hobbes", "lang", "fr")
    yield ft_client

def test_app(app):
    # requires an authentication
    app.get("/authenticated", 401, login=None)
    app.get("/authenticated", 200, "Hello", login="calvin")
    app.get("/authenticated", 200, "Bonjour", login="hobbes")
    # only allowed to calvin
    app.get("/only-admin", 401, login=None)
    app.get("/only-admin", 200, "administrateur", login="calvin")
    app.get("/only-admin", 403, "not in group", login="hobbes")
    # no authentication required, but depends on lang
    app.get("/open", 200, "Hello", login="calvin", auth="none")
    app.get("/open", 200, "Bonjour", login="hobbes", auth="none")
    app.get("/open", 200, "Guten Tag", login=None)
```

## Classes

The implementation of these fixtures is based on five classes, see the API
documentation for further details:

- `Authenticator` class to store test credentials.
- `RequestFlaskResponse` class to turn a `requests` response into
  a Flask-looking response, with the following attributes: `status_code`,
  `data`, `text`, `headers`, `cookies`, `is_json` and `json`.
- `Client` abstract class to run test, with two implementations.
- `FlaskClient` implementation class for internal (`test_client`) tests.
- `RequestClient` implementation class for external (real HTTP) tests.

## Exceptions

The following exceptions are defined and may be raised:

- `FlaskTesterError` root class for exceptions.
- `AuthError` authentication-related errors.

## See Also, or Not

- [Flask Testing](https://github.com/jarus/flask-testing) an unmaintained
  old-style unit test for Flask 1.x, without authentication help.
