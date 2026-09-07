# Bounded Source Profiling

Phase 2는 current snapshot 취득과 profiling을 분리합니다. `acquire_snapshot.py`는 v1 세 소스의 공식 `file.localdata.go.kr` bulk URL만 유한 재시도/timeout으로 취득하며 history endpoint는 호출하지 않습니다. profiler는 **이미 외부 저장소에 존재하는 CSV artifact**를 재현 가능하게 검사합니다.

## 안전 규칙

- `KBL_DATA_ROOT`는 Git 저장소 바깥이어야 합니다.
- 입력 artifact는 반드시 `KBL_DATA_ROOT` 아래에 있어야 합니다.
- 원본 파일을 수정하지 않습니다.
- SHA-256을 계산합니다.
- UTF-8 / CP949 / EUC-KR 후보를 strict decode로 검사합니다. 대체문자 방식은 사용하지 않습니다.
- CSV 행의 필드 수가 헤더와 다르면 실패합니다.
- cardinality 메모리는 컬럼당 상한을 둡니다. 상한을 넘으면 정확한 개수라고 주장하지 않고 lower bound로 기록합니다.
- raw `top_values`는 상태(status) 계열 컬럼에만 기록하며 주소·상호·식별자 후보에는 기록하지 않습니다.
- 컬럼명 기반 힌트는 의미 해석이 아니라 profiling 후보 표시일 뿐입니다.

## 실행 예시

```bash
python scripts/acquire_snapshot.py general_restaurants \
  --data-root "$KBL_DATA_ROOT"

python scripts/profile_artifact.py general_restaurants \
  "$KBL_DATA_ROOT/raw/general_restaurants/source.csv"
```

출력은 다음과 같이 외부 저장소에 생성됩니다.

```text
$KBL_DATA_ROOT/staging/profiles/<source_key>/<sha256>/
  manifest.json
  profile.json
```

`profile.json`은 스키마, 행수, null/blank, bounded cardinality, 날짜 parseability, 숫자 range, status/address/identifier/coordinate-like 컬럼명 힌트를 포함합니다. 기본키나 lifecycle 의미를 결정하지 않습니다.
