# Simple Test Flask application with authn and authz

import FlaskSimpleAuth as fsa
import secret

# create application with token, param and basic authentication
app = fsa.Flask("app", FSA_MODE="dev", FSA_AUTH=["token", "param", "basic"])

# authentication with randomly-generated passwords
PASSDB = {login: app.hash_password(pwd) for login, pwd in secret.PASSES.items()}

app.get_user_pass(lambda login: PASSDB.get(login, None))  # set hook

# admin group authorization
ADMINS: set[str] = {"calvin", "susie"}

@app.group_check("ADMIN")
def user_is_admin(login: str) -> bool:
    return login in ADMINS

# routes
@app.get("/login", authorize="ALL", auth="basic")
def get_token(user: fsa.CurrentUser):
    return {"user": user, "token": app.create_token(user)}, 200

@app.post("/login", authorize="ALL", auth="param")
def post_token(user: fsa.CurrentUser):
    return {"user": user, "token": app.create_token(user)}, 201

@app.get("/who-am-i", authorize="ALL")
def get_who_am_i(user: fsa.CurrentUser):
    return {"user": user, "isadmin": user_is_admin(user)}, 200

@app.get("/admin", authorize="ADMIN")
def get_admin(user: fsa.CurrentUser):
    return {"user": user, "isadmin": True}, 200

# for coverage
def create_app():
    return app
