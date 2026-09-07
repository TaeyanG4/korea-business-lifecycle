# Reproducibility

## Supported Python

- Python 3.11
- Python 3.12

## Local verification

```bash
python -m pip install -e ".[test,build,geo]"
python -m compileall src scripts tests
pytest -v
python scripts/repo_check.py
```

Network sockets are disabled during pytest. The `build` extra pins `pyarrow==21.0.0` for reproducible Parquet writer behavior, and the `geo` extra pins `pyproj==3.7.2` across the supported Python 3.11/3.12 matrix. Real-data artifacts remain only under the Git-ignored runtime data root.

## Git milestone gate

Every meaningful implementation milestone follows:

`test → commit → push origin/main → verify matching remote SHA → verify Python 3.11/3.12 Actions green`

Force push, including `--force-with-lease`, is prohibited.
