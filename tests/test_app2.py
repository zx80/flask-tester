import os
import pytest
from FlaskTester import ft_client, ft_authenticator

os.environ.update(FLASK_TESTER_ALLOW="basic param none")

@pytest.fixture
def app(ft_client):
    ft_client.setPass("calvin", "clv-pw")
    ft_client.setCookie("calvin", "lang", "en")
    ft_client.setPass("hobbes", "hbs-pw")
    ft_client.setCookie("hobbes", "lang", "fr")
    yield ft_client

def test_something(app):
    # requires an authentication
    app.get("/authenticated", 401, login=None)
    res = app.get("/authenticated", 200, login="calvin")
    assert "Hello" in res.text
    app.get("/authenticated", 200, "Bonjour", login="hobbes")
    # only allowed to calvin
    app.get("/only-calvin", 401, login=None)
    app.get("/only-calvin", 200, login="calvin")
    app.get("/only-calvin", 403, login="hobbes")
    # no authentication required, but depends on lang
    res = app.get("/no-auth", 200, login="calvin", auth="none")
    assert "Hello" in res.text
    app.get("/no-auth", 200, "Bonjour", login="hobbes", auth="none")
    app.get("/no-auth", 200, "Guten Tag", login=None)
