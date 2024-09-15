"""FlaskTester - Pytest fixtures for Flask authenticated internal and external tests.

PYTEST_DONT_REWRITE: local assertions are really that, not pytest assertions.
"""

import os
import io
import re
# Python >= 3.11: Self
from typing import Any, Callable
import importlib
import logging
import pytest  # for explicit fail calls, see _pytestFail
import json
import dataclasses

log = logging.getLogger("flask_tester")


class FlaskTesterError(BaseException):
    """Base exception for FlaskTester package."""
    pass


class AuthError(FlaskTesterError):
    """Authenticator Exception."""
    pass


class _AssertError(FlaskTesterError):
    """User assertion Exception, only for internal testing."""
    pass


def _pytestFail(msg: str):
    """Undocumented switch for FlaskTester own tests.

    A pytest test cannot check an expected pytest failure without failing.
    """
    log.error(msg)
    if "FLASK_TESTER_TESTING" in os.environ:
        raise _AssertError(msg)
    else:  # pragma: no cover
        pytest.fail(msg)


class Authenticator:
    """Manage HTTP request authentication.

    Supported schemes:

    - ``basic``: HTTP Basic Authentication.
    - ``param``: password with HTTP or JSON parameters.
    - ``bearer``: token in ``Authorization`` *bearer* header.
    - ``header``: token in a header.
    - ``cookie``: token in a cookie.
    - ``tparam``: token in a parameter.
    - ``fake``: fake scheme, login directly passed as a parameter.
    - ``none``: no authentication, only cookies.

    Constructor parameters:

    :param allow: List of allowed schemes.
        defaults to ``["bearer", "basic", "param", "none"]``.
    :param user: Parameter for user on ``param`` password authentication,
        defaults to ``"USER"``.
    :param pwd: Parameter for password on ``param`` password authentication,
        defaults to ``"PASS"``.
    :param login: Parameter for user on ``fake`` authentication,
        defaults to ``"LOGIN"``.
    :param bearer: Name of bearer scheme for token,
        defaults to ``"Bearer"``.
    :param header: Name of header for token,
        defaults to ``"Auth"``.
    :param cookie: Name of cookie for token,
        defaults to ``"auth"``.
    :param tparam: Name of parameter for token,
        defaults to ``"AUTH"``.
    :param ptype: Default parameter type, either *data* or *json*,
        defaults to ``"data"``.

    Note: default values are consistent with `FlaskSimpleAuth <https://pypi.org/project/FlaskSimpleAuth/>`_.
    """

    _TOKEN_SCHEMES = {"bearer", "header", "cookie", "tparam"}
    _PASS_SCHEMES = {"basic", "param"}

    # all supported authentication schemes
    _AUTH_SCHEMES = {"fake", "none"}
    _AUTH_SCHEMES.update(_TOKEN_SCHEMES)
    _AUTH_SCHEMES.update(_PASS_SCHEMES)

    # authenticator login/pass hook
    _AuthHook = Callable[[str, str|None], None]

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
             ptype: str = "data",
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
        assert ptype in ("json", "data")
        self._ptype = ptype

        # _AuthHook|None, but python cannot stand it:-(
        self._auth_hook: Any = None

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

    def setHook(self, hook: _AuthHook):
        """Set on password hook."""
        self._auth_hook = hook

    def setPass(self, login: str, pw: str|None):
        """Associate a password to a user.

        Set to *None* to remove the password entry.
        """
        if not self._has_pass:
            raise AuthError("cannot set password, no password scheme allowed")
        self._set(login, pw, self._passes)
        _ = self._auth_hook and self._auth_hook(login, pw)

    def setPasses(self, pws: list[str]):
        """Associate a list of *login:password*."""
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
        """Add request parameter to ``json`` or ``data``."""

        if "json" in kwargs:
            assert isinstance(kwargs["json"], dict)
            kwargs["json"][key] = val
        elif "data" in kwargs:
            assert isinstance(kwargs["data"], dict)
            kwargs["data"][key] = val
        else:
            kwargs[self._ptype] = {key: val}

    def _try_auth(self, auth: str|None, scheme: str) -> bool:
        """Whether to try this authentication scheme."""
        return auth in (None, scheme) and scheme in self._allow

    def setAuth(self, login: str|None, kwargs: dict[str, Any], cookies: dict[str, str], auth: str|None = None):
        """Set request authentication.

        :param login: Login target, *None* means no authentication.
        :param kwargs: Request parameters to modify.
        :param cookies: Request cookies to modify.
        :param auth: Authentication method, default is *None*.

        The default behavior is to try allowed schemes: token first,
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

    This only works for simple responses.

    Available public attributes:

    - ``status_code``: integer status code.
    - ``data``: body as bytes.
    - ``text``: body as a string.
    - ``headers``: dict of headers and their values.
    - ``cookies``: dict of cookies.
    - ``json``: JSON-converted body, or *None*.
    - ``is_json``: whether body was in JSON.

    Constructor parameter:

    :param response: Response from request.
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

    :param auth: Authenticator.
    :param default_login: When ``login`` is not set.
    """

    # client login/pass hook (with mypy workaround)
    # Python >= 3.11: Self
    AuthHook = Callable[[Any, str, str|None], None]  # type: ignore

    def __init__(self, auth: Authenticator, default_login: str|None = None):
        self._auth = auth
        self._cookies: dict[str, dict[str, str]] = {}  # login -> name -> value
        self._default_login = default_login

    def setHook(self, hook: AuthHook):
        """Set on password hook."""
        self._auth.setHook(lambda u, p: hook(self, u, p))

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

        :param method: HTTP method ("GET", "POST", "PATCH", "DELETE"…).
        :param path: Local path under the base URL.

        Optional parameters:

        :param status: Expected HTTP status, *None* to skip status check.
        :param content: Regular expression for response body, *None* to skip content check.
        :param login: Authenticated user, use **explicit** *None* to skip default.
        :param auth: Authentication scheme to use instead of default behavior.
        :param **kwargs: More request parameters (headers, data, json…).
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

        # this is forbidden by Flask client
        if "json" in kwargs and "data" in kwargs:
            # merge into data to possibly keep uploads
            kwargs["data"].update(kwargs["json"])
            del kwargs["json"]

        # convert json parameters to json
        if "json" in kwargs:
            json_param = kwargs["json"]
            assert isinstance(json_param, dict)
            for name in list(json_param.keys()):
                val = json_param[name]
                if val is None:
                    pass
                elif isinstance(val, (bool, int, float, str, tuple, list, dict)):
                    pass
                elif "model_dump" in val.__dir__() and callable(val.model_dump):
                    # probably pydantic
                    json_param[name] = val.model_dump()
                else: # pydantic or standard dataclasses?
                    json_param[name] = dataclasses.asdict(val)

        # convert data parameters to simple strings
        if "data" in kwargs:
            data_param = kwargs["data"]
            assert isinstance(data_param, dict)
            for name in list(data_param.keys()):
                val = data_param[name]
                if val is None:
                    data_param[name] = "null"
                elif isinstance(val, (io.IOBase, tuple)):
                    pass  # file parameters?
                elif isinstance(val, (bool, int, float, str)):
                    # FIXME bool seems KO
                    pass
                elif isinstance(val, (list, dict)):
                    data_param[name] = json.dumps(val)
                elif "model_dump_json" in val.__dir__() and callable(val.model_dump_json):
                    data_param[name] = val.model_dump_json()
                else:
                    data_param[name] = json.dumps(dataclasses.asdict(val))

        # now set authentication headers and do the query
        self._auth.setAuth(login, kwargs, cookies, auth=auth)
        res = self._request(method, path, cookies, **kwargs)  # type: ignore

        # check status
        if status is not None:
            if res.status_code != status:  # show error before aborting
                # FIXME what if the useful part is at the end?
                _pytestFail(f"bad {status} result: {res.status_code} {res.text[:512]}...")

        # check content
        if content is not None:
            if not re.search(content, res.text, re.DOTALL):
                # FIXME what if the useful part is at the end?
                _pytestFail(f"cannot find {content} in {res.text[:512]}...")

        return res

    def get(self, path: str, status: int|None = None, content: str|None = None, **kwargs):
        """HTTP GET request, see `Client.request`."""
        return self.request("GET", path, status=status, content=content, **kwargs)

    def post(self, path: str, status: int|None = None, content: str|None = None, **kwargs):
        """HTTP POST request, see `Client.request`."""
        return self.request("POST", path, status=status, content=content, **kwargs)

    def put(self, path: str, status: int|None = None, content: str|None = None, **kwargs):
        """HTTP PUT request, see `Client.request`."""
        return self.request("PUT", path, status=status, content=content, **kwargs)

    def patch(self, path: str, status: int|None = None, content: str|None = None, **kwargs):
        """HTTP PATCH request, see `Client.request`."""
        return self.request("PATCH", path, status=status, content=content, **kwargs)

    def delete(self, path: str, status: int|None = None, content: str|None = None, **kwargs):
        """HTTP DELETE request, see `Client.request`."""
        return self.request("DELETE", path, status=status, content=content, **kwargs)


class RequestClient(Client):
    """Request-based test provider.

    Constructor parameters:

    :param auth: Authenticator.
    :param base_url: Target server.
    :param default_login: When ``login`` is not set.
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

    :param auth: Authenticator.
    :param client: Flask actual ``test_client``.
    :param default_login: When ``login`` is not set.

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
    """Fixture implementation, separated for testing purposes."""

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
    ptype = os.environ.get("FLASK_TESTER_PTYPE", "data")

    # create authenticator, possibly with initial credentials
    auth = Authenticator(allow, user=user, pwd=pwd, login=login, bearer=bearer,
                         header=header, cookie=cookie, tparam=tparam, ptype=ptype)

    # possibly load credentials from the environment
    if "FLASK_TESTER_AUTH" in os.environ:
        auth.setPasses(os.environ["FLASK_TESTER_AUTH"].split(","))

    return auth

@pytest.fixture
def ft_authenticator():
    """Pytest Fixture: ft_authenticator.

    Environment variables:

    - ``FLASK_TESTER_LOG_LEVEL``: package log level in
      ``DEBUG INFO WARNING ERROR CRITICAL NOSET``,
      defaults to ``NOTSET``.
    - ``FLASK_TESTER_ALLOW``: allowed space-separated authentication schemes, in
      ``basic param bearer header cookie tparam fake none``,
      defaults to ``bearer basic param none``.
    - ``FLASK_TESTER_USER``: user login parameter for ``param`` authentication,
      defaults to ``USER``.
    - ``FLASK_TESTER_PASS``: user password parameter for ``param`` authentication,
      defaults to ``PASS``.
    - ``FLASK_TESTER_LOGIN``: user login parameter for ``fake`` authentication,
      defaults to ``LOGIN``.
    - ``FLASK_TESTER_BEARER``: bearer name for *token* authentication,
      defaults to ``Bearer``.
    - ``FLASK_TESTER_HEADER``: header name for *token* authentication,
      defaults to ``Auth``.
    - ``FLASK_TESTER_COOKIE``: cookie name for *token* authentication,
      defaults to ``auth``.
    - ``FLASK_TESTER_TPARAM``: parameter for *token* authentication,
      defaults to ``AUTH``.
    - ``FLASK_TESTER_PTYPE``: default parameter type, ``data`` or ``json``,
      defaults to ``data``.
    - ``FLASK_TESTER_AUTH``: initial comma-separated list of *login:password*,
      defaults to not set.
    """

    yield _ft_authenticator()

def _ft_client(authenticator):
    """Fixture implementation separated for testing."""

    default_login = os.environ.get("FLASK_TESTER_DEFAULT", None)
    client: Client

    test_app = os.environ.get("FLASK_TESTER_APP", "app")

    if test_app.startswith("http://") or test_app.startswith("https://"):
        client = RequestClient(authenticator, test_app, default_login)
    else:
        # load app package
        if ":" in test_app:  # override defaults
            pkg_name, app_name = test_app.split(":", 1)
            app_names = [app_name]
        else:
            pkg_name = test_app
            app_names = ["app", "application", "create_app", "make_app"]
        pkg = importlib.import_module(pkg_name)
        # find app in package
        app = None
        for name in app_names:
            if hasattr(pkg, name):
                app = getattr(pkg, name)
                if callable(app) and not hasattr(app, "test_client"):
                    app = app()
                break
        # none found
        if not app:
            raise FlaskTesterError(f"cannot find Flask app in {pkg_name} ({test_app})")
        client = FlaskClient(authenticator, app.test_client(), default_login)  # type: ignore

    return client

@pytest.fixture
def ft_client(ft_authenticator):
    """Pytest Fixture: ft_client.

    Mandatory target environment variable:

    - ``FLASK_TESTER_APP``: find the Flask application, eg
      ``app:create_app`` for an internal test, or
      ``http://localhost:5000`` for an external test.

    Other environment variable:

    - ``FLASK_TESTER_DEFAULT``: Default client login, default is *None* for no
      default.
    """

    yield _ft_client(ft_authenticator)
