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

세 날짜 안에서 전환이 보이지 않으면 범위를 자동 확장하지 않습니다. 별도의 새 bounded plan을 수립해야 합니다.

