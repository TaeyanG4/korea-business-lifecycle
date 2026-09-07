# Authenticated History Probe

공식 v1 Swagger는 세 카테고리 모두 `/history`를 제공하며 다음을 요구합니다.

- `serviceKey`
- `pageNo`
- `numOfRows` (최대 100)
- `cond[BASE_DATE::EQ]` — 2026-01-01부터 조회일 전일까지
- `cond[OPN_ATMY_GRP_CD::EQ]`

응답에는 `totalCount`가 있으므로 한 `(category, BASE_DATE, authority code)` query의 pagination은 유한합니다. 그러나 공식 설명은 **해당 일자 기준 상태값 조회**이므로 이를 lossless event log로 해석하지 않습니다.

현재 snapshot에서 개방자치단체코드는 세 카테고리 모두 동일하게 230개가 관찰됐고 모두 7자리 숫자였습니다. 이는 probe 입력 검증에 사용하지만 공식 전국 코드 도메인의 완전성 증거로 사용하지 않습니다.

`scripts/probe_history.py`는 page 1 한 번만 요청하고 응답 row를 저장하지 않으며 aggregate `totalCount`만 출력합니다. 인증키는 환경변수로만 전달합니다.

```powershell
$env:KBL_DATA_GO_KR_SERVICE_KEY = "<data.go.kr Decoding key>"
python scripts/probe_history.py bakeries 20260101 3000000
```

인증키를 Git, `.env` 커밋, 명령행 인자, 로그, provenance에 넣지 마십시오.
