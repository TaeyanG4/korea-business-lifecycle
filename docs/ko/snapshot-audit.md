# Current Snapshot Grain / Lifecycle Audit

`audit_snapshot.py`는 Phase 3의 longitudinal 결론을 내리기 전에 current snapshot에서 반증 가능한 사실만 측정합니다.

- `관리번호`와 `(개방자치단체코드, 관리번호)`의 null/uniqueness/duplicate를 disk-backed SQLite로 정확히 집계합니다.
- parsed field 전체의 SHA-256으로 동일 parsed-row 중복을 집계합니다. 이는 raw-byte 동일성 주장과 구분합니다.
- source `영업상태명=폐업`과 `폐업일자` 존재 여부를 교차검증합니다.
- 폐업일자 < 인허가일자, retrieval date 이후 날짜, 비파싱 날짜를 집계합니다.
- 사업장명/전화번호/도로명주소/지번주소의 비어있지 않은 행 수만 집계하며 실제 값은 audit JSON에 기록하지 않습니다.
- X/Y는 결측쌍·부분결측·숫자 parse 실패·0/음수만 검사하고 CRS transform은 수행하지 않습니다.

이 audit만으로 relocation, category change, reopening, history ordering, longitudinal identifier stability를 판단하지 않습니다. 해당 항목은 history API가 필요합니다.
