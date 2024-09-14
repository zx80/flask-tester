# application suitable for the documentation example

import FlaskSimpleAuth as fsa
import secret

def create_app():

    app = fsa.Flask("app", FSA_MODE="dev", FSA_AUTH=["basic", "param", "none"])

    # app password, group and other data
    PASSDB = {login:app.hash_password(pw) for login, pw in secret.PASSES.items()}
    ADMIN = {"calvin", "susie"}
    HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Guten Tag"}

    # minimal authentication and authorization configuration
    app.get_user_pass(PASSDB.get)
    app.group_check("admin", ADMIN.__contains__)

    # 4 routes
    @app.get("/open", authorize="OPEN")
    def get_no_auth(lang: fsa.Cookie = "de"):
        return fsa.jsonify(HELLO.get(lang, "Hey"))

    @app.get("/authenticated", authorize="AUTH")
    def get_authenticated(user: fsa.CurrentUser, lang: fsa.Cookie = "de"):
        return fsa.jsonify(HELLO.get(lang, "Hey") + " " + user)

    @app.get("/only-admin", authorize="admin")
    def get_only_admin():
        return fsa.jsonify("Salut administrateur !")

    @app.get("/add", authorize="OPEN")
    def get_add(i: int, j: int):
        return {"sum": i + j}

    return app
