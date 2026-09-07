# v1 Current Snapshot 관찰 결과

2026-09-07에 세 전국 current snapshot을 Git 외부에 취득하고 SHA-256으로 고정한 뒤 전체 파일을 프로파일링/감사했습니다.

- 일반음식점: 2,295,369행 / 696,584,488 bytes
- 휴게음식점: 645,952행 / 207,347,981 bytes
- 제과점영업: 69,481행 / 22,654,977 bytes
- 합계: **3,010,802행 / 926,587,446 bytes**
- 세 파일 모두 CP949, 39컬럼이며 exact column intersection과 union이 모두 39입니다.
- `관리번호`는 각 snapshot 내부 및 세 카테고리 사이에서 현재 관찰상 중복이 없었습니다. 이는 PK 선언이나 longitudinal 안정성 증명이 아닙니다.
- 휴게음식점은 `영업상태명=폐업`인데 `폐업일자`가 비어 있는 10건, 일반음식점은 561건이 있어 `폐업일자 != null` 단독 규칙은 반증되었습니다.
- 일반음식점에는 비어있지 않지만 파싱되지 않는 인허가일자 4건과 retrieval date 이후 폐업일자 3건이 있습니다.
- 전화번호·사업장명·정확 주소·홈페이지·정밀 좌표가 실제 스키마에 존재하므로 public row-level allowlist는 승인하지 않았습니다.

이 결과는 current snapshot에 한정됩니다. authenticated history probe는 구현되어 있으나, 2026-09-07 실제 제과점 `/info`와 `/history` 호출에서 현재 로컬 키가 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`로 거부되었습니다. 따라서 relocation, reopening, category transition, history ordering, longitudinal identifier stability는 유효한 data.go.kr 서비스키/활용권한이 확인될 때까지 판단하지 않습니다.
