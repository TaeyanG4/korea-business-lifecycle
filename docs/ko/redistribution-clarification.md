# Optional Redistribution Written Clarification

확인일: **2026-09-08**

세 v1 행정안전부 OpenAPI 상세 페이지 모두 `이용허락범위 제한 없음`을 표시하므로 source-use metadata gate는 `PASS_METADATA_CONFIRMED`입니다. 그러나 공공데이터포털 정책은 공공데이터에 제3자 권리가 포함된 경우 권리자의 정당한 이용허락이 필요하다고 명시합니다.

현재 상세 페이지에서는 이 세 source에 제3자 권리가 **없다**고 별도로 선언한 문구를 확인하지 못했습니다. 이 부재 자체를 제3자 권리 부재의 법적 증명으로 사용하지는 않습니다. 다만 세 source의 공식 표시가 모두 `이용허락범위 제한 없음`인 점을 최종 v1 release decision의 운영 근거로 삼아 **검증된 privacy-minimized aggregate 공개는 승인**했습니다. Row-level mirror는 계속 별도 검토 대상으로 남깁니다.

## 선택적으로 서면 확인할 질문

1. 세 API의 `이용허락범위 제한 없음`이 Kaggle 같은 제3자 플랫폼에 row-level source record를 재배포/mirror하는 것까지 허용하는가?
2. 이 세 데이터셋에 공공데이터포털 정책상 별도 허락이 필요한 제3자 권리가 포함되어 있는가?
3. row-level mirror가 불가하거나 조건부라면, direct/linkable row field와 precise coordinates를 제외하고 k=10 미만 셀을 suppress한 derived aggregate는 외부 재배포 가능한가?
4. 허용되는 경우 필요한 출처표시, notice, 공공누리 유형 또는 기타 조건은 무엇인가?

## 확인 경로

- 공공데이터포털 `문의하기`
- 운영자 메일 상담: `opendata_help@nia.or.kr`
- 대표전화: `1566-0025`
- 제공기관: 행정안전부
- 관리부서: 지역디지털협력과

자동으로 메일이나 문의를 전송하지 않습니다. 회신을 받으면 source-specific written evidence로 보관해 향후 row-level 또는 더 넓은 공개범위를 재검토할 수 있습니다. **현재 aggregate Kaggle 공개에는 회신이 필수가 아닙니다.**

## 준비된 문의안

제목: `행정안전부 지방행정 인허가정보 3종 외부 재배포 가능 여부 서면 확인 요청`

문의 대상 source를 다음처럼 명시합니다.

- `15154916` 일반음식점
- `15154921` 휴게음식점
- `15155252` 제과점영업

본문은 `provenance/redistribution_clarification_plan.json`의 `prepared_inquiry.body_ko`에 고정했습니다. Kaggle row-level mirror, 제3자 권리, privacy-minimized aggregate, 필요한 출처표시/공공누리/notice 조건을 한 번에 묻고, `k=10`을 법적 개인정보 안전 보장으로 주장하지 않는다는 점도 명시합니다. 상태는 `READY_NOT_SENT`이며 자동 전송하지 않습니다.

## 현재 상태

- source-use metadata: PASS
- raw external mirror: `UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION`
- privacy-minimized aggregate redistribution: `APPROVED_BY_V1_RELEASE_SCOPE`
- row-level public release: BLOCKED
- aggregate publication: APPROVED
- outreach performed: false
- written response received: false

최신 기계 판독 결정은 `provenance/v1_release_scope.json`이며, 기존 `provenance/redistribution_clarification_plan.json`은 당시의 보수적 문의 계획을 감사 추적용으로 보존합니다.
