# Reproducibility

## Supported Python

- Python 3.11
- Python 3.12

## Local verification

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
python scripts/repo_check.py
```

Network sockets are disabled during pytest. Future real-data integration tests will be opt-in and will reference approved artifacts stored outside Git.

## Git milestone gate

Every meaningful implementation milestone follows:

`test → commit → push origin/main → verify matching remote SHA → verify Python 3.11/3.12 Actions green`

Force push, including `--force-with-lease`, is prohibited.
