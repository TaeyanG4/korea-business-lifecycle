# 첫 실행 마일스톤: Food-Service v1 Feasibility

## 결정

현재 상태는 **`FEASIBLE_FOR_BOUNDED_PROFILING_ONLY`** 입니다.

진행 가능한 범위:

- 세 v1 소스의 bounded schema/profile 실험 설계
- license/privacy 증거 보강
- finite history protocol 검증
- source identifier/status/date/coordinate 필드 검증

아직 진행하지 않는 범위:

- 전체 history 크롤링
- 기본키 확정
- 폐업/생존 라벨 생성
- 실데이터 Git 커밋
- Kaggle 공개
- 나머지 192개 카테고리 구현

## 현재 blocker

1. history의 하한/retention/완전성과 유한 종료 규칙
2. Kaggle 원자료 재배포 권리
3. 공개 필드 privacy allowlist
4. establishment/permit identity 의미
5. closure/lifecycle 의미
6. 실제 좌표 X/Y 필드 의미 및 축 순서

`provenance/feasibility.json`이 기계 판독 가능한 gate 원본입니다.
