# SMS to Todoist Bridge

This simple function will bridge todoist and twilio. 

It's designed to be run as a serverless function.

## Runtime and dependencies

Use Python 3.12. The dependency refresh raises the original Python 3.6 runtime
requirement; an existing serverless deployment must be moved to Python 3.12
before using this lockfile. This repository does not manage that deployment.

Install the exact dependency graph with Pipenv (the lockfile was generated with
Pipenv 2026.11.0):

```sh
pipenv sync
pipenv verify
pipenv run python -m pip check
```

`Pipfile.lock` includes updated certifi, PyJWT, urllib3, and their aligned
consumer/transitive dependencies. Continue using the lockfile rather than an
unconstrained install of the Pipfile's wildcard requirements.

## Local verification

```sh
pipenv run python -m unittest discover -s tests -v
pipenv run python -m compileall -q main.py tests
pipenv requirements --hash > /path/to/requirements.txt
pipenv run python -m pip wheel --require-hashes -r /path/to/requirements.txt -w /path/to/wheels
```

The tests exercise SMS priority mapping, real TwiML serialization/XML escaping,
Todoist request serialization through Requests, and PyJWT signature verification.
Only external Todoist I/O is replaced. They do not create tasks or send SMS.
Live Todoist service compatibility and serverless deployment are not verified;
`todoist-python` emits a deprecation warning recommending `todoist-api-python`.
Migrating the Todoist integration is separate from this dependency refresh.

For vulnerability checks, install `pip-audit` in a separate tooling environment
and audit the application's installed site-packages with `pip-audit --path`.
Do not ignore advisories to make this check pass.

