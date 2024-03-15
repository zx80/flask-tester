# Simple Test Flask application with authn and authz

import FlaskSimpleAuth as fsa

app = fsa.Flask("app", FSA_MODE="dev", FSA_AUTH=["token", "param", "basic"])

# authentication with randomly-generated passwordss
import secret
PASSDB = {login: app.hash_password(pwd) for login, pwd in secret.PASSES.items()}

@app.get_user_pass
def get_user_pass(login: str) -> str|None:
    return PASSDB.get(login, None)

# authorization
ADMINS: set[str] = {"calvin", "susie"}

@app.group_check("ADMIN")
def user_is_admin(login: str) -> bool:
    return login in ADMINS

# routes
@app.get("/token", authorize="ALL", auth="basic")
def get_token(user: fsa.CurrentUser):
    return {"user": user, "token": app.create_token(user)}, 200

@app.post("/token", authorize="ALL", auth="param")
def post_token(user: fsa.CurrentUser):
    return {"user": user, "token": app.create_token(user)}, 201

@app.get("/who-am-i", authorize="ALL")
def get_who_am_i(user: fsa.CurrentUser):
    return {"user": user, "isadmin": user in ADMINS}, 200

@app.get("/admin", authorize="ADMIN")
def get_admin(user: fsa.CurrentUser):
    return {"user": user, "isadmin": True}, 200

# for coverage
def create_app():
    return app
