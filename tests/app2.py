# application suitable for the documentation example

import FlaskSimpleAuth as fsa

def create_app():

    app = fsa.Flask("app2", FSA_AUTH=["basic", "param"])

    # authentication
    PASSES = {"calvin": "clv-pw", "hobbes": "hbs-pw"}
    PASSDB = {l: app.hash_password(p) for l, p in PASSES.items()}
    app.get_user_pass(lambda l: PASSDB.get(l, None))

    # authorization
    CALVIN = {"calvin"}
    app.group_check("CALVIN", lambda l: l in CALVIN)

    HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Guten Tag"}

    # 3 routes
    @app.get("/authenticated", authorize="AUTH")
    def get_authenticated(user: fsa.CurrentUser, lang: fsa.Cookie = "de"):
        return fsa.jsonify(HELLO.get(lang, "Hey") + " " + user), 200

    @app.get("/only-calvin", authorize="CALVIN")
    def get_only_calvin():
        return "Salut Calvin!", 200

    @app.get("/no-auth", authorize="OPEN")
    def get_no_auth(lang: fsa.Cookie = "de"):
        return fsa.jsonify(HELLO.get(lang, "Hey")), 200

    return app
