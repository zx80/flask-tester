# FlaskTester - Pytest fixtures for Flask internal and external authenticated tests

This package allows to run authenticated tests against a Flask application,
either with internal Flask tests (aka `test_client`) or external tests (with
`requests` which performs actual HTTP requests), including password and token
authentication and per-user cookies.

Only one set of tests is needed, switching from internal to external is
achieved by setting an environment variable.

![Status](https://github.com/zx80/flask-tester/actions/workflows/package.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-16%20✓-success)
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

def authHook(api, user: str, pwd: str|None):
    if pwd is not None:  # get a token when a login/password is provided
        res = api.get("/login", login=user, auth="basic", status=200)
        api.setToken(user, res.json["token"])
    else:  # remove token
        api.setToken(user, None)

@pytest.fixture
def app(ft_client):
    # register authentication hook
    ft_client.setHook(authHook)
    # add test passwords for Calvin and Hobbes (must be consistent with app!)
    ft_client.setPass("calvin", secret.PASSES["calvin"])
    ft_client.setPass("hobbes", secret.PASSES["hobbes"])
    # also set a cookie
    ft_client.setCookie("hobbes", "lang", "fr")
    ft_client.setCookie("calvin", "lang", "en")
    # return working client
    yield ft_client

def test_app_admin(app):
    app.get("/admin", login=None, status=401)
    for auth in ["bearer", "basic", "param"]:
        res = app.get("/admin", login="calvin", auth=auth, status=200)
        assert res.json["user"] == "calvin" and res.json["isadmin"]
        res = app.get("/admin", login="hobbes", auth=auth, status=403)
        assert 'not in group "ADMIN"' in res.text
```

This can be run against a local or remote server:

```shell
export TEST_SEED="some-random-data"              # shared test seed
flask --app app:app run &                        # start flask app
pid=$!                                           # keep pid
export FLASK_TESTER_APP="http://localhost:5000"  # set app url, local or remote
pytest test.py                                   # run external tests
kill $pid                                        # stop app with pid
```

Or locally with the Flask internal test infrastructure:

```shell
export FLASK_TESTER_APP="app:app"                # set app package
pytest test.py                                   # run internal tests
```

The above test runs with [`tests/app.py`](tests/app.py)
[Flask](https://flask.palletsprojects.com/)
REST application back-end with password and token authentication based on
[FlaskSimpleAuth](https://pypi.org/project/FlaskSimpleAuth/).
The code uses _23_ lines of Python for implementing
password (basic and parameters) and token authentications,
admin group authorization, and routes for
token generation (2), identity tests (2) and an incredible open cookie-based
translation service.

See the [documentation](https://zx80.github.io/flask-tester/).

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence… Beware that you may lose your
hairs or your friends because of it. If you like it, feel free to send a
postcard to the author.

## Versions

Packages are distributed from [PyPI](https://pypi.org/project/FlaskTester/),
[sources](https://github.com/zx80/flask-tester) are available on GitHub,
please report any [issues](https://github.com/zx80/flask-tester/issues).
