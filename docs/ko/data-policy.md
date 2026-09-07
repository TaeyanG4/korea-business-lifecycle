# 데이터 및 개인정보 정책

## Git에 포함하지 않는 것

- 원본/bulk 데이터
- staging/processed 전국 데이터
- 로그
- 인증키와 credential
- 비공개 prompt/task 파일
- 로컬 AI/agent 지침
- 검토 전 개인정보·연락처 필드

실데이터는 기본적으로 저장소 내부의 Git-ignored `data/local/`에서 다룹니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓰는 경우 `data/local/` 하위만 허용합니다.

## 공개 접근과 재배포

2026-09-07 재검수에서 일반음식점·휴게음식점·제과점영업의 공식 행정안전부 OpenAPI 상세 페이지 모두 `이용허락범위 제한 없음`을 다시 확인했습니다. 따라서 **source-use metadata gate는 PASS**로 분리합니다. 다만 각 상세 페이지의 라이선스 섹션에서 제3자 권리 존재 여부를 별도로 확정하는 문구는 확인하지 못했고, 공공데이터포털 이용정책은 제3자 권리가 포함된 경우 권리자의 정당한 이용허락 확보를 요구합니다. 문구의 부재를 제3자 권리 부재의 증명으로 사용하지 않으므로 raw Kaggle mirror와 privacy-minimized aggregate의 외부 재배포 gate는 계속 `UNRESOLVED`입니다.

## 개인정보

사업장명과 소재지주소는 upstream 설명에서 공개 필드로 확인되지만, 이 프로젝트의 전국 단위 재배포에 적합한지는 별도 검토합니다. row-level public build는 계속 금지합니다. 별도 aggregate 후보는 직접 식별/연결 가능 필드와 precise coordinates를 제외하고 exact date를 연도로 축약하며 k=10 미만 셀을 suppress하지만, 이 기술적 최소화도 개인정보 안전 또는 재배포 허가를 자동 보장하지 않습니다.
