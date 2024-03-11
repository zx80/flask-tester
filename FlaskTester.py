import os
import io
import re
from typing import Any
import importlib
import logging
import pytest

log = logging.getLogger("flask_tester")
log.setLevel(level=logging.DEBUG)

class FlaskTesterError(BaseException):
    pass


class AuthError(FlaskTesterError):
    pass


class Authenticator:
    """Manage authentication for test requests.

    Supported schemes:
    - ``basic``: HTTP Basic Authentication
    - ``param``: password with HTTP or JSON parameters
    - ``bearer``: token in ``Authorization`` _bearer_ header
    - ``header``: token in a header
    - ``cookie``: token in a cookie
    - ``tparam``: token in a parameter
    - ``fake``: fake scheme, login directly passed as a parameter
    """

    _AUTH_SCHEMES = ("basic", "param", "bearer", "header", "cookie", "tparam", "fake")

    def __init__(self,
             allow: list[str] = ["bearer", "basic", "param"],
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
        """Constructor parameters:

        - ``allow``: list of allowed schemes.
          default is ``["bearer", "basic", "param"]``
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

        for auth in allow:
            assert auth in self._AUTH_SCHEMES
        self._allow = allow

        # authentication scheme parameters
        self._user = user
        self._pass = pwd
        self._login = login
        self._bearer = bearer
        self._header = header
        self._cookie = cookie
        self._tparam = tparam

        # password and token credentials
        self._passes: dict[str, str] = {}
        self._tokens: dict[str, str] = {}

    def _set(self, login: str, val: str|None, store: dict[str, str]):
        """Set a key/value in a directory, with None for delete."""
        if val is None:
            if login in store:
                del store[login]
        else:
            store[login] = val

    def setPass(self, login: str, pw: str|None):
        """Associate a password to a user."""
        self._set(login, pw, self._passes)

    def setPasses(self, pws: list[str]):
        """Associate a list of login:password."""
        for lp in pws:
            login, pw = lp.split(":", 1)
            self.setPass(login, pw)

    def setToken(self, login: str, token: str|None):
        """Associate a token to a user."""
        self._set(login, token, self._tokens)

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

    def setAuth(self, login: str|None, kwargs: dict[str, Any], auth: str|None = None):
        """Set request authentication.

        - login: login target, None means no authentication
        - kwargs: request parameters
        - auth: authentication method, default None is to try allowed schemes, tokens first.
        """

        log.debug(f"setAuth: login={login} auth={auth} allow={self._allow}")

        if login is None:  # not needed
            return

        if auth is not None:
            if auth not in self._AUTH_SCHEMES:
                raise AuthError(f"unexpected auth: {auth}")
            if auth not in self._allow:
                raise AuthError(f"auth is not allowed: {auth}")

        # use token if available and allowed
        if login in self._tokens and auth in (None, "bearer", "header", "cookie", "tparam"):

            token = self._tokens[login]

            if "headers" not in kwargs:
                kwargs["headers"] = {}

            if self._try_auth(auth, "bearer"):
                kwargs["headers"]["Authorization"] = self._bearer + " " + token
            elif self._try_auth(auth, "header"):
                kwargs["headers"][self._header] = token
            elif self._try_auth(auth, "tparam"):
                self._param(kwargs, self._tparam, token)
            elif self._try_auth(auth, "cookie"):
                # FIXME cookie?
                kwargs["headers"]["Cookie"] = self._cookie + "=" + token
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

        else:
            raise AuthError(f"no authentication for login={login} auth={auth} allow={self._allow}")


class RequestFlaskResponse:
    """Wrapper to return a Flask-looking response from a request response.

    This only work for simple responses.

    Available attributes:
    - status_code: integer status code
    - data: body as bytes
    - text: body as a string
    - headers: dict of headers and their values
    - cookies: dict of cookies
    - json: JSON-converted body, or None
    - is_json: whether body was in JSON
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
    """Common class for flask authenticated testing."""

    def __init__(self, auth: Authenticator, default_login: str|None = None):
        self._auth = auth
        self._default_login = default_login

    def setToken(self, login: str, token: str|None):
        """Associate a token to a login, None to remove."""
        self._auth.setToken(login, token)

    def setPass(self, login: str, password: str|None):
        """Associate a password to a login, None to remove."""
        self._auth.setPass(login, password)

    def _request(self, method: str, path: str, **kwargs):
        """Run a request and return response."""
        raise NotImplementedError()

    def request(self, method: str, path: str, status: int|None = None, auth: str|None = None, **kwargs):
        """Run a possibly authenticated HTTP request.

        Mandatory parameters:
        - method: HTTP method ("GET", "POST", "PATCH", "DELETE"…)
        - path: local path under the base URL

        Optional parameters:
        - status: expected HTTP status, None to skip status check
        - login: authenticated user, use **explicit** None to skip
        - auth: authentication schme to use
        - **kwargs: more request parameters (headers, data, json…)
        """

        if "login" in kwargs:
            login = kwargs["login"]
            del kwargs["login"]
        else:  # if unset, use default
            login = self._default_login

        self._auth.setAuth(login, kwargs, auth=auth)
        res = self._request(method, path, **kwargs)  # type: ignore

        if status is not None:
            if res.status_code != status:  # show error before aborting
                log.error(f"bad {status} result: {res.status_code} {res.text[:512]}")
            assert res.status_code == status

        return res

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def check(self, method: str, path: str, status: int, content: str|None = None, **kwargs):
        """Run a query and check the response.

        Mandatory parameters:
        - method: HTTP method ("GET", "POST", "PATCH", "DELETE"…)
        - path: local path under the base URL
        - status: expected HTTP status

        Optional parameters:
        - content: regular expression in response body
        - login: authenticated user, use explicit None to skip
        - **kwargs: more request parameters (headers, data, json…)
        """

        # get HTTP response
        res = self.request(method, path, status=status, **kwargs)

        if content is not None:
            if not re.search(content, res.text, re.DOTALL):
                log.error(f"cannot find {content} in {res.text}")
                assert False, "content not found"

        return res


class RequestClient(Client):
    """Request-based test provider."""

    def __init__(self, auth: Authenticator, base_url: str, default_login=None):
        super().__init__(auth, default_login)
        self._base_url = base_url
        # reuse connections, otherwise it is too slow…
        from requests import Session
        self._requests = Session()

    def _request(self, method: str, path: str, **kwargs):
        # ensure file upload compatibility
        if "data" in kwargs:
            data = kwargs["data"]
            files: dict[str, Any] = {}
            for name, whatever in data.items():
                # FIXME what types should be accepted?
                if isinstance(whatever, io.BufferedReader):
                    files[name] = whatever
                elif isinstance(whatever, tuple):
                    # reorder tuple to match requests expectations:
                    file_handle, file_name, file_type = whatever
                    files[name] = (file_name, file_handle, file_type)
                else:
                    pass
            # complete "data" to "files" parameter transfer
            for name in files:
                del data[name]
            assert "files" not in kwargs
            kwargs["files"] = files
            # sanity
            assert not (files and "json" in kwargs), "cannot mix file upload and json?"
        res = self._requests.request(method, self._base_url + path, **kwargs)
        return RequestFlaskResponse(res)


class FlaskClient(Client):
    """Flask-based test provider."""

    def __init__(self, auth: Authenticator, client, default_login=None):
        super().__init__(auth, default_login)
        self._client = client

    def _request(self, method: str, path: str, **kwargs):
        return self._client.open(method=method, path=path, **kwargs)


@pytest.fixture
def ft_authenticator():
    allow = os.environ["FLASK_TESTER_ALLOW"].split(" ") if "FLASK_TESTER_ALLOW" in os.environ else ["bearer", "basic", "param"]
    auth = Authenticator(allow)
    if "FLASK_TESTER_AUTH" in os.environ:
        auth.setPasses(os.environ["FLASK_TESTER_AUTH"].split(","))
    yield auth 


@pytest.fixture
def ft_client(ft_authenticator):
    client: Client
    if "FLASK_TESTER_URL" in os.environ:
        app_url = os.environ["FLASK_TESTER_URL"]
        client = RequestClient(ft_authenticator, app_url)
    elif "FLASK_TESTER_APP" in os.environ:
        pkg_name = os.environ["FLASK_TESTER_APP"]
        pkg = importlib.import_module(pkg_name)
        if hasattr(pkg, "app"):
            app = getattr(pkg, "app")
        elif hasattr(pkg, "create_app"):
            app = getattr(pkg, "create_app")()
        else:
            raise FlaskTesterError(f"cannot find Flask app in {pkg_name}")
        client = FlaskClient(ft_authenticator, app.test_client())
    else:
        raise FlaskTesterError("no Flask application to test")
    yield client
