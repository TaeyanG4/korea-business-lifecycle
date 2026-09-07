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

2026-09-08 재검수에서 일반음식점·휴게음식점·제과점영업의 공식 행정안전부 OpenAPI 상세 페이지 모두 `이용허락범위 제한 없음`을 다시 확인했습니다. **source-use metadata gate는 PASS**입니다. 공공데이터포털 정책은 제3자 권리가 실제 포함된 경우 정당한 이용허락을 요구하므로, 문구의 부재를 제3자 권리 부재의 법적 증명으로 사용하지 않습니다. 최신 v1 release scope는 **canonical 3,010,802행 row-level PERMIT 공개를 승인**하며 현재 Kaggle 제품은 이 current snapshot 하나로 통합했습니다. 과거 privacy-minimized aggregate는 검증된 파생물/감사 증적으로 남지만 별도 Kaggle dataset은 더 이상 운영하지 않습니다. Canonical source EPSG:5174 좌표는 row-level release에 포함되며, 별도로 파생한 WGS84 sidecar와 partial history는 계속 공개하지 않습니다. 별도 서면 문의는 [Optional Redistribution Written Clarification](redistribution-clarification.md)에 추가 assurance 용도로 남깁니다.

## 개인정보

최신 공개 승인에 따라 canonical row-level release는 사업장명, 주소, 관리번호, 원천 EPSG:5174 좌표 등 canonical 26컬럼을 유지합니다. 별도 aggregate는 여전히 직접/연결 가능 필드와 정밀좌표를 제외하고 exact date를 연도로 축약하며 k=10 미만 셀을 suppress합니다. **k=10 자체를 법적 개인정보 안전 보장으로 주장하지 않습니다.** 전화번호/홈페이지는 canonical parent에 포함되지 않아 row-level 공개본에도 없습니다.
