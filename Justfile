# NOTE: This file is exempt from cookiecutter templating
build: mypy && _test check-format
    # Build project
    pyproject-build

test: mypy && check-format
    # Testing project
    @just _test

mypy:
    mypy src
    PYTHONPATH=src mypy tests

# runs tests without anything else
_test:
    PYTHONPATH=src pytest tests

# Checks for formatting issues
check-format: (format "--check")

format *flags:
    black {{ flags }} -- .
    isort {{ flags }} -- .
