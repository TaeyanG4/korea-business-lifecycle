# 03→01 전환 후속 Probe

확장 표본 audit에서 `03→01` 전이가 2건 관찰됐습니다. 두 건 모두 폐업일자가 값에서 빈값으로 바뀌었고, 인허가일·사업장명·주소·좌표는 두 끝점에서 유지됐습니다.

이번 후속 단계는 전국 history 수집이 아닙니다. 종료 snapshot의 `LAST_MDFCN_PNT` 날짜를 후보일로 사용해 각 사례의 전날/당일/다음날만 조회합니다.

- 휴게음식점 / `3830000`: `2026-08-31`, `2026-09-01`, `2026-09-02`
- 일반음식점 / `4530000`: `2026-03-16`, `2026-03-17`, `2026-03-18`

총 6 snapshot이며 네트워크 요청 상한은 411회입니다. 실제 `MNG_NO`, 사업장명, 주소, 좌표, 폐업일자 값은 public output에 기록하지 않습니다.

## 실행

Dry-run:

```powershell
python scripts/acquire_reverse_transition_probes.py
```

실제 수집:

```powershell
python scripts/acquire_reverse_transition_probes.py --execute
```

완료 후 aggregate-only 감사:

```powershell
python scripts/audit_reverse_transition_probes.py
```

## 실행 결과

6개 snapshot 수집과 aggregate-only audit이 완료됐습니다.

- 휴게음식점 / `3830000`: `2026-08-31`에는 `03 / 폐업`, `2026-09-01`부터 `01 / 영업/정상`
- 일반음식점 / `4530000`: `2026-03-16`에는 `03 / 폐업`, `2026-03-17`부터 `01 / 영업/정상`
- 두 사례 모두 상세상태도 `02 / 폐업 → 01 / 영업`
- 두 사례 모두 폐업일자는 `값 → 빈값`
- 두 사례 모두 인허가일·사업장명·주소·좌표는 probe 전체에서 유지

따라서 **source-level 상태 역전 자체는 확인**됐습니다. `03 / 폐업`을 영구적인 terminal closure로 가정하는 규칙은 반증됐습니다.

다만 이 상태 역전이 실제 현실의 **재개업**인지, 행정 데이터의 **정정/복원**인지는 이 API만으로 확정하지 않습니다. 따라서 향후 lifecycle 모델은 irreversible terminal event가 아니라 reopening-aware episode 또는 multi-state 모델을 우선 고려합니다.

기계 판독 결과는 `provenance/reverse_transition_findings.json`에 있습니다. 원문 `MNG_NO`, 상호, 주소, 좌표, 폐업일자 값은 저장소에 커밋하지 않습니다.
