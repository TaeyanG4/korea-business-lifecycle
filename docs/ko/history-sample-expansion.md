# History 표본 확장 계획

기존 `3000000` 한 곳의 bounded longitudinal audit을 완료한 뒤, 현재 전국 snapshot의 세 카테고리 합산 행 수를 기준으로 규모 분포에서 네 곳을 추가 선정했습니다.

| 층 | 자치단체코드 | 현재 합산 행 수 | 두 시점 예상 API 요청 수 |
|---|---:|---:|---:|
| q10 | `4420000` | 1,984 | 43 |
| q50 | `4530000` | 9,323 | 188 |
| q90 | `3830000` | 28,136 | 561 |
| max | `3220000` | 70,649 | 1,400 |

추가 표본은 `2026-01-01`과 `2026-09-06`, 세 v1 카테고리만 조회합니다. 기존 baseline을 포함하면 총 다섯 자치단체가 됩니다. 네 곳 추가 수집의 probe 기반 예상 요청량은 **2,192 requests**입니다.

이는 통계적으로 전국을 대표하는 확률표본이 아닙니다. 목적은 데이터 규모가 크게 다른 자치단체에서도 `MNG_NO` continuity, status/closure 변화, status vocabulary drift가 일관되는지 확인하는 것입니다.

## 안전한 실행

먼저 네트워크를 사용하지 않는 dry-run을 실행합니다.

```powershell
python scripts/acquire_history_sample.py
```

실제 수집은 명시적 `--execute`가 필요합니다.

```powershell
python scripts/acquire_history_sample.py --execute
```

실행기는 tracked plan 밖의 자치단체/날짜/카테고리를 확장하지 않고, 총 예상 요청량이 2,500을 넘으면 중단합니다. 완료된 snapshot은 재실행 시 건너뛰므로 중단 후 재개할 수 있습니다. 실제 service key는 로컬 `.env` 또는 환경변수에서만 읽고 출력/manifest에 저장하지 않습니다.

수집 완료 후 다음 명령으로 aggregate-only audit을 생성합니다.

```powershell
python scripts/audit_history_sample.py --authority 4420000 --authority 4530000 --authority 3830000 --authority 3220000
```
