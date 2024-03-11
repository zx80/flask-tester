import os
import pytest
import FlaskSimpleAuth as fsa
import FlaskTester as ft
from FlaskTester import ft_client, ft_authenticator
import app
import logging

logging.basicConfig(level=logging.INFO)

# set authn from for ft_authenticator
os.environ.update(
    FLASK_TESTER_ALLOW="bearer basic param",
    FLASK_TESTER_AUTH=",".join(f"{l}:{p}" for l, p in app.PASSES.items()),
)

# must provide url or package of Flask application to test
assert "FLASK_TESTER_URL" in os.environ or "FLASK_TESTER_APP" in os.environ

@pytest.fixture
def api(ft_client):
    # bad password / token
    ft_client._auth.setPass("moe", "bad password")
    ft_client._auth.setToken("moe", "bad token")
    # get valid tokens using password authn
    res = ft_client.get("/token", login="calvin", auth="basic", status=200)
    assert res.json["user"] == "calvin"
    ft_client._auth.setToken("calvin", res.json["token"])
    res = ft_client.post("/token", login="hobbes", auth="param", status=201, data={})
    assert res.json["user"] == "hobbes"
    ft_client._auth.setToken("hobbes", res.json["token"])
    res = ft_client.post("/token", login="susie", auth="param", status=201, json={})
    assert res.json["user"] == "susie"
    ft_client._auth.setToken("susie", res.json["token"])
    # check that token auth is ok
    res = ft_client.get("/who-am-i", login="calvin", status=200, auth="bearer")
    assert res.json["user"] == "calvin"
    res = ft_client.get("/who-am-i", login="hobbes", status=200, auth="bearer")
    assert res.json["user"] == "hobbes"
    res = ft_client.get("/who-am-i", login="susie", status=200, auth="bearer")
    assert res.json["user"] == "susie"
    # add a bad password
    yield ft_client

def test_admin(api):
    # check authentication schemes
    for auth in (None, "basic", "param", "bearer"):
        api.get("/admin", status=200, login="calvin", auth=auth)
        api.check("GET", "/admin", 200, login="susie", auth=auth)
        api.check("GET", "/admin", 403, login="hobbes", auth=auth)
        api.check("GET", "/admin", 401, login="moe", auth=auth)
        api.check("GET", "/admin", 401, login=None, auth=auth)

def test_errors(api):
    for scheme in ("header", "cookie", "fake", "tparam"):
        try:
            api.get("/token", login="calvin", auth=scheme)
            assert False, "must raise an exception"
        except ft.AuthError as e:
            assert True, "expected error"
