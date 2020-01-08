# logger_lib_python

lib to format log in json


## FORMAT CODE BEFORE COMMIT

Execute pre-commit: 

```bash
pre-commit install
```

Resolve code with `BLACK` before commit:

```bash
black --line-length 120 --target-version py37 .
```

Valid code with `FLAKE8` before commit:

```bash
flake8 --max-line-length=120 --ignore=F401,W503,E203 .
```