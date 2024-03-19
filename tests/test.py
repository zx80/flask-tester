import os
import pytest
import FlaskSimpleAuth as fsa
import FlaskTester as ft
from FlaskTester import ft_client, ft_authenticator
import secret
import http.server as htsv
import threading
import io
import logging

logging.basicConfig(level=logging.INFO)

# set authn for ft_authenticator
os.environ.update(
    FLASK_TESTER_ALLOW="bearer basic param",
    FLASK_TESTER_AUTH=",".join(f"{l}:{p}" for l, p in secret.PASSES.items()),
)

def test_sanity():
    # must provide url or package of Flask application to test
    assert "FLASK_TESTER_URL" in os.environ or "FLASK_TESTER_APP" in os.environ

# example from README.md
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

@pytest.fixture
def api(ft_client):
    # set a default
    ft_client._default_login = "calvin"
    # bad password / token
    ft_client.setPass("moe", None)
    ft_client.setToken("moe", None)
    ft_client.setPass("moe", "bad password")
    ft_client.setToken("moe", "bad token")
    # get valid tokens using password authn
    res = ft_client.get("/login", login="calvin", auth="basic", status=200)
    assert res.json["user"] == "calvin"
    ft_client._auth.setToken("calvin", res.json["token"])
    res = ft_client.post("/login", login="hobbes", auth="param", status=201, data={})
    assert res.json["user"] == "hobbes"
    ft_client._auth.setToken("hobbes", res.json["token"])
    res = ft_client.post("/login", login="susie", auth="param", status=201, json={})
    assert res.json["user"] == "susie"
    ft_client._auth.setToken("susie", res.json["token"])
    # check that token auth is ok
    res = ft_client.get("/who-am-i", login="calvin", status=200, auth="bearer")
    assert res.json["user"] == "calvin"
    res = ft_client.get("/who-am-i", login="hobbes", status=200, auth="bearer")
    assert res.json["user"] == "hobbes"
    res = ft_client.get("/who-am-i", login="susie", status=200, auth="bearer")
    assert res.json["user"] == "susie"
    # with defaults
    res = ft_client.get("/who-am-i", auth="basic", status=200)
    assert res.json["user"] == "calvin"
    res = ft_client.get("/who-am-i", auth="param", status=200)
    assert res.json["user"] == "calvin"
    res = ft_client.get("/who-am-i", auth="bearer", status=200)
    assert res.json["user"] == "calvin"
    res = ft_client.get("/who-am-i", status=200)
    assert res.json["user"] == "calvin"
    # add a bad password
    yield ft_client

def test_admin(api):
    # check authentication schemes
    for auth in (None, "basic", "param", "bearer"):
        api.check("GET", "/admin", status=200, login="calvin", auth=auth)
        api.check("GET", "/admin", 200, login="susie", auth=auth)
        api.check("GET", "/admin", 403, login="hobbes", auth=auth)
        api.check("GET", "/admin", 401, login="moe", auth=auth)
        api.check("GET", "/admin", 401, login=None, auth=auth)
        try:
            api.check("GET", "/admin", status=599, login="calvin", auth=auth)
            pytest.fail("assert on status must fail")  # pragma: no cover
        except AssertionError as e:
            assert "200" in str(e)
        try:
            api.check("GET", "/admin", status=200, login="calvin", auth=auth, content="NOT THERE")
            pytest.fail("assert on content must fail")  # pragma: no cover
        except AssertionError as e:
            assert "NOT THERE" in str(e)

def test_errors(api):
    for scheme in ("header", "cookie", "fake", "tparam", "unexpected"):
        try:
            api.get("/login", login="calvin", auth=scheme)
            pytest.fail("must raise an exception")  # pragma: no cover
        except ft.AuthError as e:
            assert True, "expected error"

def test_methods(api):
    api.get("/who-am-i", login="hobbes", status=200)
    api.post("/who-am-i", login="hobbes", status=405)
    api.put("/who-am-i", login="hobbes", status=405)
    api.patch("/who-am-i", login="hobbes", status=405)
    api.delete("/who-am-i", login="hobbes", status=405)

def test_authenticator_token():
    # all token carriers
    auth = ft.Authenticator(allow=["bearer", "header", "tparam", "cookie"])
    auth.setToken("calvin", "clv-token")
    auth.setToken("susie", "ss-token")
    auth.setToken("hobbes", "hbs-token")
    auth.setToken("moe", "m-token")
    kwargs = {}
    auth.setAuth("calvin", kwargs, auth="bearer")
    assert kwargs["headers"]["Authorization"] == "Bearer clv-token"
    kwargs = {}
    auth.setAuth("susie", kwargs, auth="header")
    assert kwargs["headers"]["Auth"] == "ss-token"
    kwargs = {"data": {}}
    auth.setAuth("hobbes", kwargs, auth="tparam")
    assert kwargs["data"]["AUTH"] == "hbs-token"
    kwargs = {"json": {}}
    auth.setAuth("hobbes", kwargs, auth="tparam")
    assert kwargs["json"]["AUTH"] == "hbs-token"
    kwargs = {}
    auth.setAuth("moe", kwargs, auth="cookie")
    assert kwargs["headers"]["Cookie"] == "auth=m-token"
    # dad does not have a token
    try:
        kwargs = {}
        auth.setAuth("dad", kwargs)
        pytest.fail("must raise an error")  # pragma: no cover
    except ft.FlaskTesterError:
        assert True, "error raised"
    # rosalyn as a password, but no password carrier is allowed
    try:
        auth.setPass("rosalyn", "rsln-pass")
        pytest.fail("must raise an error")  # pragma: no cover
    except ft.AuthError:
        assert True, "error raised"
    # force to trigger later errors
    auth._has_pass = True
    auth.setPass("rosalyn", "rsln-pass")
    try:
        kwargs={}
        auth.setAuth("rosalyn", kwargs)
        pytest.fail("must raise an error")  # pragma: no cover
    except ft.FlaskTesterError:
        assert True, "error raised"

def test_authenticator_password():
    # all password carriers plus fake
    auth = ft.Authenticator(allow=["basic", "param", "fake"])
    auth.setPass("calvin", "clv-pass")
    auth.setPass("hobbes", "hbs-pass")
    auth.setPass("moe", "m-pass")
    auth.setPass("rosalyn", "rsln-pass")
    kwargs = {}
    auth.setAuth("calvin", kwargs, auth="basic")
    assert kwargs["auth"] == ("calvin", "clv-pass")
    kwargs = {"data": {}}
    auth.setAuth("hobbes", kwargs, auth="param")
    assert kwargs["data"]["USER"] == "hobbes" and kwargs["data"]["PASS"] == "hbs-pass"
    kwargs = {"json": {}}
    auth.setAuth("moe", kwargs, auth="param")
    assert kwargs["json"]["USER"] == "moe" and kwargs["json"]["PASS"] == "m-pass"
    kwargs = {"data": {}}
    auth.setAuth("rosalyn", kwargs, auth="fake")
    assert kwargs["data"]["LOGIN"] == "rosalyn"
    kwargs = {"json": {}}
    auth.setAuth("hobbes", kwargs, auth="fake")
    assert kwargs["json"]["LOGIN"] == "hobbes"
    # susie as a token, but no token carrier is allowed
    try:
        auth.setToken("susie", "ss-token")
        pytest.fail("must raise an error")  # pragma: no cover
    except ft.FlaskTesterError:
        assert True, "error raised"
    # force to trigger later error
    auth._has_token = True
    auth.setToken("susie", "ss-token")
    try:
        kwargs={}
        auth.setAuth("susie", kwargs)
        pytest.fail("must raise an error")  # pragma: no cover
    except ft.FlaskTesterError:
        assert True, "error raised"

def test_request_flask_response():

    class RequestResponse:
        """Local class for testing RequestFlaskResponse."""

        def __init__(self, is_json: bool):
            self._is_json = is_json
            self.status_code = 200
            self.content = b"hello world!"
            self.text = "hello world!"
            self.headers = {"Server": "test/0.1"}
            self.cookies = {}

        def json(self):
            if self._is_json:
                return {"hello": "world!"}
            else:
                raise Exception("not json!")

    jres = ft.RequestFlaskResponse(RequestResponse(True))
    assert jres.is_json and jres.json is not None

    xres = ft.RequestFlaskResponse(RequestResponse(False))
    assert not xres.is_json and xres.json is None

def test_client():
    client = ft.Client(ft.Authenticator())
    try:
        client._request("GET", "/")
        pytest.fail("must raise an error")  # pragma: no cover
    except NotImplementedError:
        assert True, "expected error raised"

def test_request_client():
    httpd = htsv.HTTPServer(("", 8888), htsv.SimpleHTTPRequestHandler)
    thread = threading.Thread(target = lambda: httpd.serve_forever())
    thread.start()
    try:
        client = ft.RequestClient(ft.Authenticator(), "http://localhost:8888")
        client.get("/", status=200)
        hello = io.BytesIO(b"hello world")
        client.post("/", status=501, data={"hello": hello})
        hello = io.BytesIO(b"hello world")
        client.post("/", status=501, data={"hello": (hello, "hello.txt", "text/plain")})
        client.post("/", status=501, data={"hello": "world!"})
    finally:
        httpd.shutdown()
