# 재현성

## 지원 Python

- Python 3.11
- Python 3.12

## 로컬 검증

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
python scripts/repo_check.py
```

`pytest` 실행 중 네트워크 socket은 차단됩니다. 향후 실데이터 integration test는 Git 외부의 승인된 artifact를 명시적으로 지정하는 opt-in 테스트로만 추가합니다.

## Git 마일스톤

모든 의미 있는 구현 마일스톤은 다음 순서를 따릅니다.

`test → commit → push origin/main → remote SHA 일치 확인 → Python 3.11/3.12 Actions 성공 확인`

force push, `--force-with-lease`를 포함한 강제 ref 업데이트는 사용하지 않습니다.

