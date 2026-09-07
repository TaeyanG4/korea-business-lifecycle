# Canonical PERMIT Full-Snapshot Dry Run

확인일: **2026-09-07**

실제 current snapshot 전체를 frozen 26컬럼 `PERMIT` transformer에 **스트리밍으로 통과시키되 canonical row를 저장하지 않는** dry-run validator를 구현했고, 사용자가 전체 3,010,802행 실행까지 완료했습니다.

## 실행 범위

- `general_restaurants`: 2,295,369행
- `rest_cafes`: 645,952행
- `bakeries`: 69,481행
- 합계: 3,010,802행
- 네트워크 호출: 없음
- canonical CSV/Parquet/ZSTD 출력: 없음
- row-level 값 stdout/stderr 출력: 없음

실행 전 latest retrieval manifest의 artifact SHA-256/bytes가 `observed_snapshot_summary.json`의 현재 증거와 일치하는지 확인합니다. 다른 artifact가 latest가 되면 fail-closed하며 기존 증거를 조용히 재사용하지 않습니다.

## Streaming 검증

각 source row를 한 번에 하나씩 strict CSV decode/parse하여 frozen `PERMIT` transformer에 전달합니다. 결과 row는 메모리에 누적하거나 파일에 기록하지 않고 다음 aggregate만 누적합니다.

- 변환된 행 수
- permit/closure date quality 건수
- null X/Y 건수
- source/canonical column count
- duplicate linkage candidate 여부

`source_key + management_number` uniqueness는 메모리에 300만 identifier를 유지하지 않기 위해 `data/local/.tmp/canonical-full-dry-run/` 아래의 임시 SQLite primary-key index로 정확히 검사합니다. 정상 완료 및 처리된 오류에서는 임시 DB를 삭제합니다. 강제 종료나 시스템 장애가 발생하면 ignored local temp 파일이 남을 수 있으므로 재실행 전 해당 temp 디렉터리를 확인할 수 있습니다.

## 진행률

기본적으로 50,000행마다 stderr에 다음 형태의 aggregate 진행률을 출력합니다.

```text
[1/3] START general_restaurants full dry-run rows=2,295,369
[1/3] ROWS general_restaurants 100,000/2,295,369 (4.4%) | overall 100,000/3,010,802 (3.3%)
[1/3] DONE general_restaurants rows=2,295,369 | overall 2,295,369/3,010,802 (76.2%)
```

관리번호, 사업장명, 주소, 전화번호, 좌표값은 진행률에 포함하지 않습니다. 최종 aggregate JSON만 stdout에 출력합니다.

## 안전 장치

`--execute`를 주지 않으면 실제 scan을 시작하지 않고 실행 plan만 출력합니다.

```powershell
python scripts/dry_run_full_current_snapshot.py
```

실제 전체 실행은 별도 승인된 장시간 로컬 작업입니다.

```powershell
python scripts/dry_run_full_current_snapshot.py --execute
```

한 source만 재검증할 수도 있습니다.

```powershell
python scripts/dry_run_full_current_snapshot.py --execute --source bakeries
```

## 현재 상태

전체 3,010,802행이 모두 `PASS`했습니다. `source_key + management_number` 중복은 0건이었고 임시 uniqueness index는 세 source 모두 정상 삭제됐습니다. permit-date quality는 `VALID` 3,010,798행 / `INVALID` 4행이며, 이 4건은 이전 full profiling에서 이미 관찰된 anomaly count와 일치합니다. closure-date quality는 `VALID` 2,115,684행 / `MISSING` 895,118행입니다.

aggregate-only 결과는 `provenance/permit_parent_full_dry_run.json`에 고정했습니다. 다음 gate는 동일 SHA-256 source에 대한 local-only production `PERMIT` Parquet/ZSTD materialization입니다.
