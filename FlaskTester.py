"""FlaskTester - Pytest fixtures for Flask authenticated internal and external tests.

Pytest: PYTEST_DONT_REWRITE
"""

import os
import io
import re
from typing import Any
import importlib
import logging
import pytest

log = logging.getLogger("flask_tester")


class FlaskTesterError(BaseException):
    """Base exception for FlaskTester package."""
    pass


class AuthError(FlaskTesterError):
    """Authenticator Exception."""
    pass


class Authenticator:
    """Manage authentication for test requests.

    Supported schemes:

    - ``basic``: HTTP Basic Authentication
    - ``param``: password with HTTP or JSON parameters
    - ``bearer``: token in ``Authorization`` *bearer* header
    - ``header``: token in a header
    - ``cookie``: token in a cookie
    - ``tparam``: token in a parameter
    - ``fake``: fake scheme, login directly passed as a parameter
    - ``none``: no authentication, only cookies

    Constructor parameters:

    - ``allow``: list of allowed schemes.
      default is ``["bearer", "basic", "param", "none"]``
    - ``user``: parameter for user on ``param`` password authentication,
      default is ``USER``
    - ``pwd``: parameter for password on ``param`` password authentication,
      default is ``PASS``
    - ``login``: parameter for user on ``fake`` authentication,
      default is ``LOGIN``
    - ``bearer``: name of bearer scheme for token,
      default is ``Bearer``
    - ``header``: name of header for token,
      default is ``Auth``
    - ``cookie``: name of cookie for token,
      default is ``auth``
    - ``tparam``: name of parameter for token,
      default is ``AUTH``
    """

    _TOKEN_SCHEMES = {"bearer", "header", "cookie", "tparam"}
    _PASS_SCHEMES = {"basic", "param"}

    # all supported authentication schemes
    _AUTH_SCHEMES = {"fake", "none"}
    _AUTH_SCHEMES.update(_TOKEN_SCHEMES)
    _AUTH_SCHEMES.update(_PASS_SCHEMES)

    def __init__(self,
             allow: list[str] = ["bearer", "basic", "param", "none"],
             # parameter names for "basic" and "param"
             user: str = "USER",
             pwd: str = "PASS",
             # parameter name for "fake"
             login: str = "LOGIN",
             # 4 token options
             bearer: str = "Bearer",
             header: str = "Auth",
             cookie: str = "auth",
             tparam: str = "AUTH",
         ):

        self._has_pass, self._has_token = False, False
        for auth in allow:
            assert auth in self._AUTH_SCHEMES
            if auth in self._TOKEN_SCHEMES:
                self._has_token = True
            if auth in self._PASS_SCHEMES:
                self._has_pass = True
        self._allow = allow

        # authentication scheme parameters
        self._user = user
        self._pass = pwd
        self._login = login
        self._bearer = bearer
        self._header = header
        self._cookie = cookie
        self._tparam = tparam

        # password and token credentials, cookies
        self._passes: dict[str, str] = {}
        self._tokens: dict[str, str] = {}
        self._cookies: dict[str, dict[str, str]] = {}

    def _set(self, key: str, val: str|None, store: dict[str, str]):
        """Set a key/value in a directory, with None for delete."""
        if val is None:
            if key in store:
                del store[key]
        else:
            assert isinstance(val, str)
            store[key] = val

    def setPass(self, login: str, pw: str|None):
        """Associate a password to a user.

        Set to *None* to remove the password entry.
        """
        if not self._has_pass:
            raise AuthError("cannot set password, no password scheme allowed")
        self._set(login, pw, self._passes)

    def setPasses(self, pws: list[str]):
        """Associate a list of login:password."""
        for lp in pws:
            login, pw = lp.split(":", 1)
            self.setPass(login, pw)

    def setToken(self, login: str, token: str|None):
        """Associate a token to a user.

        Set to *None* to remove the token entry.
        """
        if not self._has_token:
            raise AuthError("cannot set token, no token scheme allowed")
        self._set(login, token, self._tokens)

    def setCookie(self, login: str, name: str, val: str|None = None):
        """Associate a cookie and its value to a login, *None* to remove."""
        if login not in self._cookies:
            self._cookies[login] = {}
        self._set(name, val, self._cookies[login])

    def _param(self, kwargs: dict[str, Any], key: str, val: Any):
        """Add request parameter to "json" or "data"."""

        if "json" in kwargs:
            assert isinstance(kwargs["json"], dict)
            kwargs["json"][key] = val
        elif "data" in kwargs:
            assert isinstance(kwargs["data"], dict)
            kwargs["data"][key] = val
        else:
            kwargs["data"] = {key: val}

    def _try_auth(self, auth: str|None, scheme: str) -> bool:
        """Whether to try this authentication scheme."""
        return auth in (None, scheme) and scheme in self._allow

    def setAuth(self, login: str|None, kwargs: dict[str, Any], cookies: dict[str, str], auth: str|None = None):
        """Set request authentication.

        - login: login target, None means no authentication
        - kwargs: request parameters
        - cookies: request cookies
        - auth: authentication method, default is None

        The default behavior is to try allowed schemes: tokens first,
        then password, then fake.
        """

        log.debug(f"setAuth: login={login} auth={auth} allow={self._allow}")

        if login is None:  # not needed
            return

        cookies.update(self._cookies.get(login, {}))

        if auth is not None:
            if auth not in self._AUTH_SCHEMES:
                raise AuthError(f"unexpected auth: {auth}")
            if auth not in self._allow:
                raise AuthError(f"auth is not allowed: {auth}")

        headers = kwargs.get("headers", {})

        # use token if available and allowed
        if login in self._tokens and auth in (None, "bearer", "header", "cookie", "tparam"):

            token = self._tokens[login]

            if self._try_auth(auth, "bearer"):
                headers["Authorization"] = self._bearer + " " + token
            elif self._try_auth(auth, "header"):
                headers[self._header] = token
            elif self._try_auth(auth, "tparam"):
                self._param(kwargs, self._tparam, token)
            elif self._try_auth(auth, "cookie"):
                cookies[self._cookie] = token
            else:
                raise AuthError(f"no token carrier: login={login} auth={auth} allow={self._allow}")

        elif login in self._passes and auth in (None, "basic", "param"):

            if self._try_auth(auth, "basic"):
                kwargs["auth"] = (login, self._passes[login])
            elif self._try_auth(auth, "param"):
                self._param(kwargs, self._user, login)
                self._param(kwargs, self._pass, self._passes[login])
            else:
                raise AuthError(f"no password carrier: login={login} auth={auth} allow={self._allow}")

        elif self._try_auth(auth, "fake"):

            self._param(kwargs, self._login, login)

        elif self._try_auth(auth, "none"):

            pass

        else:

            raise AuthError(f"no authentication for login={login} auth={auth} allow={self._allow}")

        if headers:  # put headers back if needed
            kwargs["headers"] = headers


class RequestFlaskResponse:
    """Wrapper to return a Flask-looking response from a request response.

    This only work for simple responses.

    Available attributes:

    - ``status_code``: integer status code
    - ``data``: body as bytes
    - ``text``: body as a string
    - ``headers``: dict of headers and their values
    - ``cookies``: dict of cookies
    - ``json``: JSON-converted body, or None
    - ``is_json``: whether body was in JSON

    Constructor parameter:

    - ``response``: from request.
    """

    def __init__(self, response):

        self._response = response
        self.status_code = response.status_code
        self.data = response.content
        self.text = response.text
        self.headers = response.headers
        self.cookies = response.cookies
        try:
            self.json = response.json()
            self.is_json = True
        except Exception:
            self.json = None
            self.is_json = False


class Client:
    """Common (partial) class for flask authenticated testing.

    Constructor parameters:

    - ``auth`` authenticator
    - ``default_login`` if ``login`` is not set.
    """

    def __init__(self, auth: Authenticator, default_login: str|None = None):
        self._auth = auth
        self._cookies: dict[str, dict[str, str]] = {}  # login -> name -> value
        self._default_login = default_login

    def setToken(self, login: str, token: str|None):
        """Associate a token to a login, *None* to remove."""
        self._auth.setToken(login, token)

    def setPass(self, login: str, password: str|None):
        """Associate a password to a login, *None* to remove."""
        self._auth.setPass(login, password)

    def setCookie(self, login: str, name: str, val: str|None):
        """Associate a cookie to a login, *None* name to remove."""
        self._auth.setCookie(login, name, val)

    def _request(self, method: str, path: str, cookies: dict[str, str], **kwargs):
        """Run a request and return response."""
        raise NotImplementedError()

    def request(self, method: str, path: str, status: int|None = None, content: str|None = None,
                auth: str|None = None, **kwargs):
        """Run a possibly authenticated HTTP request.

        Mandatory parameters:

        - ``method``: HTTP method ("GET", "POST", "PATCH", "DELETE"…)
        - ``path``: local path under the base URL

        Optional parameters:

        - ``status``: expected HTTP status, *None* to skip status check
        - ``content``: regular expression for response body, *None* to skip content check
        - ``login``: authenticated user, use **explicit** *None* to skip
        - ``auth``: authentication scheme to use instead of default behavior
        - ``**kwargs``: more request parameters (headers, data, json…)
        """

        if "login" in kwargs:
            login = kwargs["login"]
            del kwargs["login"]
        else:  # if unset, use default
            login = self._default_login

        cookies: dict[str, str] = {}
        if "cookies" in kwargs:
            cookies.update(kwargs["cookies"])
            del kwargs["cookies"]

        self._auth.setAuth(login, kwargs, cookies, auth=auth)
        res = self._request(method, path, cookies, **kwargs)  # type: ignore

        # check status
        if status is not None:
            if res.status_code != status:  # show error before aborting
                log.error(f"bad {status} result: {res.status_code} {res.text[:512]}")
            assert res.status_code == status, f"unexpected status {res.status_code}, expecting {status}"

        # check content
        if content is not None:
            if not re.search(content, res.text, re.DOTALL):
                log.error(f"cannot find {content} in {res.text}")
                assert False, f"expected content {content} not found in {res.text}"

        return res

    def get(self, path, **kwargs):
        """HTTP GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        """HTTP POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        """HTTP PUT request."""
        return self.request("PUT", path, **kwargs)

    def patch(self, path, **kwargs):
        """HTTP PATCH request."""
        return self.request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        """HTTP DELETE request."""
        return self.request("DELETE", path, **kwargs)

    def check(self, method: str, path: str, status: int, content: str|None = None, **kwargs):
        """Run a query and check the response status.

        Same as ``request``, but ``status`` is mandatory.
        """

        return self.request(method, path, status=status, content=content, **kwargs)


class RequestClient(Client):
    """Request-based test provider.

    Constructor parameters:

    - ``auth`` authenticator
    - ``base_url`` target server
    - ``default_login`` if ``login`` is not set.
    """

    def __init__(self, auth: Authenticator, base_url: str, default_login=None):
        super().__init__(auth, default_login)
        self._base_url = base_url
        # reuse connections, otherwise it is too slow…
        from requests import Session
        self._requests = Session()

    def _request(self, method: str, path: str, cookies: dict[str, str], **kwargs):
        """Actual request handling."""

        if "data" in kwargs:
            # "data" to "files" parameter transfer
            data = kwargs["data"]
            files: dict[str, Any] = {}
            for name, whatever in data.items():
                # FIXME what types should be accepted?
                if isinstance(whatever, io.IOBase):
                    files[name] = whatever
                elif isinstance(whatever, tuple):
                    # reorder tuple to match requests expectations:
                    file_handle, file_name, file_type = whatever
                    files[name] = (file_name, file_handle, file_type)
                else:
                    pass
            for name in files:
                del data[name]
            assert "files" not in kwargs
            kwargs["files"] = files
            # sanity
            assert not (files and "json" in kwargs), "cannot mix file upload and json?"

        res = self._requests.request(method, self._base_url + path, cookies=cookies, **kwargs)

        return RequestFlaskResponse(res)


class FlaskClient(Client):
    """Flask-based test provider.

    Constructor parameters:

    - ``auth`` authenticator
    - ``client`` Flask actual ``test_client``
    - ``default_login`` if ``login`` is not set.

    Note: this client handles `cookies`.
    """

    def __init__(self, auth: Authenticator, client, default_login=None):
        super().__init__(auth, default_login)
        self._client = client
        self._cookie_names: set[str] = set()  # FIXME all encountered cookies for cleanup :-/

    def _request(self, method: str, path: str, cookies: dict[str, str], **kwargs):
        """Actual request handling."""

        # hack to cleanup client state :-/
        for cookie in self._cookie_names:
            self._client.delete_cookie(cookie)

        for cookie, val in cookies.items():
            if cookie not in self._cookie_names:
                self._cookie_names.add(cookie)
            self._client.set_cookie(cookie, val)

        return self._client.open(method=method, path=path, **kwargs)

def _ft_authenticator():
    """Fixture implementation separated for testing."""

    level = os.environ.get("FLASK_TESTER_LOG_LEVEL", "NOTSET")
    log.setLevel(logging.DEBUG if level == "DEBUG" else
                 logging.INFO if level == "INFO" else
                 logging.WARNING if level == "WARNING" else
                 logging.ERROR if level == "ERROR" else
                 logging.CRITICAL if level == "CRITICAL" else
                 logging.NOTSET)

    allow = os.environ.get("FLASK_TESTER_ALLOW", "bearer basic param none").split(" ")

    # per-scheme parameters, must be consistent with FSA configuration
    user = os.environ.get("FLASK_TESTER_USER", "USER")
    pwd = os.environ.get("FLASK_TESTER_PASS", "PASS")
    login = os.environ.get("FLASK_TESTER_LOGIN", "LOGIN")
    bearer = os.environ.get("FLASK_TESTER_BEARER", "Bearer")
    header = os.environ.get("FLASK_TESTER_HEADER", "Auth")
    cookie = os.environ.get("FLASK_TESTER_COOKIE", "auth")
    tparam = os.environ.get("FLASK_TESTER_TPARAM", "AUTH")

    # create authenticator, possibly with initial credentials
    auth = Authenticator(allow, user=user, pwd=pwd, login=login, bearer=bearer, header=header, cookie=cookie, tparam=tparam)

    if "FLASK_TESTER_AUTH" in os.environ:
        auth.setPasses(os.environ["FLASK_TESTER_AUTH"].split(","))

    return auth

@pytest.fixture
def ft_authenticator():
    """Pytest Fixture: ft_authenticator.

    Environment variables:

    - ``FLASK_TESTER_LOG_LEVEL``: package log level in
      ``DEBUG INFO WARNING ERROR CRITICAL NOSET``.
      Default is ``NOTSET``.
    - ``FLASK_TESTER_ALLOW``: allowed space-separated authentication schemes, in
      ``basic param bearer header cookie tparam fake none``.
      Default is ``bearer basic param none``.
    - ``FLASK_TESTER_USER``: user login parameter for ``param`` authentication.
      Default is ``USER``.
    - ``FLASK_TESTER_PASS``: user password parameter for ``param`` authentication.
      Default is ``PASS``.
    - ``FLASK_TESTER_LOGIN``: user login parameter for ``fake`` authentication.
      Default is ``LOGIN``.
    - ``FLASK_TESTER_BEARER``: bearer name for *token* authentication.
      Default is ``Bearer``.
    - ``FLASK_TESTER_HEADER``: header name for *token* authentication.
      Default is ``Auth``.
    - ``FLASK_TESTER_COOKIE``: cookie name for *token* authentication.
      Default is ``auth``.
    - ``FLASK_TESTER_TPARAM``: parameter for *token* authentication.
      Default is ``AUTH``.
    - ``FLASK_TESTER_AUTH``: initial comma-separated list of *login:password*.
      Default is not set.
    """

    yield _ft_authenticator()

def _ft_client(authenticator):
    """Fixture implementation separated for testing."""

    default_login = os.environ.get("FLASK_TESTER_DEFAULT", None)
    client: Client

    if "FLASK_TESTER_URL" in os.environ:

        app_url = os.environ["FLASK_TESTER_URL"]
        client = RequestClient(authenticator, app_url, default_login)

    elif "FLASK_TESTER_APP" in os.environ:

        # load app package
        pkg_name, app = os.environ["FLASK_TESTER_APP"], None
        app_names = ["app", "application", "create_app", "make_app"]
        if ":" in pkg_name:  # override defaults
            pkg_name, app_name = pkg_name.split(":", 1)
            app_names = [app_name]
        pkg = importlib.import_module(pkg_name)
        # find app in package
        for name in app_names:
            if hasattr(pkg, name):
                app = getattr(pkg, name)
                if callable(app) and not hasattr(app, "test_client"):
                    app = app()
                break
        if not app:
            raise FlaskTesterError(f"cannot find Flask app in {pkg_name}")
        client = FlaskClient(authenticator, app.test_client(), default_login)

    else:

        raise FlaskTesterError("no Flask application to test")

    return client

@pytest.fixture
def ft_client(ft_authenticator):
    """Pytest Fixture: ft_client.

    Target environment variable, one **must** be defined:

    - ``FLASK_TESTER_URL``: application HTTP base URL.
    - ``FLASK_TESTER_APP``: Flask application, eg ``app:create_app``.

    Other environment variable:

    - ``FLASK_TESTER_DEFAULT``: Default client login, default is *None* for no
      default.
    """

    yield _ft_client(ft_authenticator)
