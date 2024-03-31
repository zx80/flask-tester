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

def test_something(app):
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
