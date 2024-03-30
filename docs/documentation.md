# FlaskTester Documentation

This is the documentation for the fixtures and support classes provided
by `FlaskTester`.

## Fixtures

The package provides two fixtures:

- `ft_authenticator` for app authentication, which depends on environment variables:

  - `FLASK_TESTER_ALLOW` space-separated list of allowed authentication schemes,
    default is `["bearer", "basic", "param", "none"]`.
  - `FLASK_TESTER_AUTH` comma-separated list of _login:password_ credentials.
  - `FLASK_TESTER_USER` user login parameter for `param` password authentication,
    default is `USER`.
  - `FLASK_TESTER_PASS` user password parameter for `param` password authentication,
    default is `PASS`.
  - `FLASK_TESTER_LOGIN` user login parameter for `fake` authentication,
    default is `LOGIN`.
  - `FLASK_TESTER_TPARAM` token parameter for `tparam` token authentication,
    default is `AUTH`.
  - `FLASK_TESTER_BEARER` bearer scheme for `bearer` token authentication,
    default is `Bearer`.
  - `FLASK_TESTER_HEADER` header name for for `header` token authentication,
    default is `Auth`.
  - `FLASK_TESTER_COOKIE` cookie name for for `cookie` token authentication,
    default is `auth`.
  - `FLASK_TESTER_PTYPE` default type of parameters, `data` or `json`,
    default is `data`.
  - `FLASK_TESTER_LOG_LEVEL` log level for module,
    default is `NOTSET`.

  The fixture has 4 main methods:
  - `setPass` to associate a password to a user, set to _None_ to remove credential.
  - `setToken` to associate a token to a user, set to _None_ to remove credential.
  - `setCookie` to add a cookie to a user, set value to _None_ to remove cookie.
  - `setAuth` to add authentication data to a request `kwargs` and `cookies`.  
    This method is called automatically for adding credentials to a request.

- `ft_client` for app testing, which depends on the previous fixture, plus
  environment variables which allow to find the application, at least one must
  be defined:

  - `FLASK_TESTER_URL` URL of the running application for external tests.
    The application is expected to be already running when the test is started.

  - `FLASK_TESTER_APP` package (filename without `.py`) to be imported for the application.
    - for `pkg:name`, `name` is the application in `pkg`.
    - for `pkg` only, look for app as `app`, `application`, `create_app`, `make_app`.
    - in both cases, `name` is called if callable and not a Flask application.

  Moreover:
  - `FLASK_TESTER_DEFAULT` default login for authentication, default is _None_.

  The fixture then provides test methods to issue test requests against a Flask application:
  - `request` generic request with `login`, `auth`, `status` end `content` extensions.
  - `get post put patch delete` methods with `login`, `auth` and `status` extensions.  
  Moreover, `setPass`, `setToken` and `setCookie` are forwarded to the internal authenticator.

Authenticator environment variables can be set from the pytest Python test file by
assigning them through `os.environ`.

## Classes

The implementation of these fixtures is based on five classes plus exceptions:

- `Authenticator` class to store test credentials.

  Use `setPass` and `setToken` to add user credentials.

- `RequestFlaskResponse` class to turn a `requests` response into
  a Flask-looking response, with the following attributes: `status_code`,
  `data`, `text`, `headers`, `cookies`, `is_json` and `json`.

- `Client` abstract class to run test, with two implementations.

  The class provides usual `get`, `post`… per-HTTP-method methods,
  and a more generic `request` method.

  These methods expect the following named parameters:

  - `login` for user login to use for authentication.
  - `auth` for the authentication scheme to use for this request,
    otherwise allowed schemes are tried, with tokens first.
  - `status` for the expected HTTP status code.

- `FlaskClient` implementation class for internal tests.

   This class is mostly the standard `test_client` with the above parameters
   extensions.

- `RequestClient` implementation class for external (real HTTP) tests.

  The path is relative to the URL provided to the constructor.

  File parameters in `data`, with the format expected by the Flask test client,
  are turned into `files` parameters as expected by `requests`.

- The following exceptions are defined:
  - `FlaskTesterError` root class for exceptions.
  - `AuthError` authentication-related errors.

## See Also, or Not

- [Flask Testing](https://github.com/jarus/flask-testing) an unmaintained
  old-style unit test for Flask 1.x, without authentication help.