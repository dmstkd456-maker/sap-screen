# 대시보드 개발자 가이드

## 소유 영역
- 라우트: `app/routes/dashboard.py`
- 데이터 집계: `app/services/dashboard_data.py`
- 데이터 로더: `app/services/data_loader.py`
- 템플릿: `templates/dashboard/dashboard.html` (메인+하위 뷰 공용)
- 스타일: `static/css/dashboard.css`, 공통 레이아웃 `static/css/layout.css`
- JS: `static/js/dashboard.js` (Chart.js 렌더)
- 공통 레이아웃/사이드바: `templates/layout.html`
- 캐시 버전: `.env`의 `ASSET_VERSION`을 템플릿에서 쿼리파라미터로 전달하여 정적 자산 캐싱 우회

## 데이터
- 기본 파일: `data/total_data.csv`
- 환경변수:
  - `SAP_TOTAL_DATA_PATH` (공용 파일)
  - `SAP_DASHBOARD_TOTAL_DATA` (대시보드 전용 지정 시)
- 전처리: `dashboard_data.preprocess`에서 날짜/년월/수치 컬럼 변환.

## 라우트 구조
- `/dashboard/` : 전체 데이터 대시보드
- `/dashboard/<view>` : 전기(electric), 기계(mechanical), 장치(instrument), 계기(meter) 필터 뷰
- view 설정: `VIEW_CONFIG` (WorkCtr 목록, 라벨맵, nav_active)
- payload 생성: `_build_payload(df)` → 8개 차트 데이터 반환

## 차트/집계 (dashboard_data.py)
- trend_by_cost_center : 호기/반 월간 건수
- damage_trend : Damage 그룹 월간 건수
- cost_center_pie : 호기 비율 파이
- workctr_pie : 작업반 비율 도넛
- cost_monthly : 월별 비용(전체/인건비/자재/기타)
- workctr_time : 작업반별 Actual Work
- equipment_damage : Equipment별 Damage 스택 (TOP N)
- status_by_cost : 호기별 완료/진행 스택
- 색상 팔레트: BASE_COLORS

## 템플릿/JS
- `templates/dashboard/dashboard.html`에 8개 `<canvas>` 고정.
- 데이터는 `<script id="dashboard-data" type="application/json">`로 전달 후 `static/js/dashboard.js`에서 Chart.js 생성.
- Chart.js는 CDN에서 `defer`로 로드. 추가 차트는 payload 집계 + 캔버스 + JS 설정을 `dashboard.js`에 추가.
- 스타일/테마는 shadcn-like 스타일(Zinc/Slate 테마, 깔끔한 카드 UI).

## 작업 가이드
- 집계 추가: dashboard_data.py에 함수 추가 → `_build_payload`에서 포함 → 템플릿에 캔버스 추가 + `static/js/dashboard.js`에 Chart 생성 코드 추가.
- 뷰 추가: VIEW_CONFIG에 view 정의, 라우트는 공용 템플릿 재사용.
- 필터링/상호작용: 현재는 정적 렌더; 프론트 필터를 추가하려면 `static/js/dashboard.js`로 JS 분리해 상태 관리 추천.
- nav_active는 사이드바 활성화를 위해 렌더 시 필수.

## 테스트
- `uv run python app.py` 후 `/dashboard/` 및 `/dashboard/<view>` 확인.
- test_client 예: `/dashboard/electric`, `/dashboard/mechanical`, `/dashboard/meter`, `/dashboard/instrument` 200 여부.

## 주의
- 데이터가 빈 경우 HTTP 500/404를 돌려 사용자에게 안내. 운영 시 사용자 친화적 메시지/가드 로직 추가 검토.
- 값이 없는 수치 컬럼은 0으로 변환해 시각화 오류 방지.
