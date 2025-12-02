# SAP Data Portal 구조/기능 개요

## 실행
- 기본 실행: `uv run python app.py`
- 데이터 파일: 기본 `data/total_data.csv` (환경변수 `SAP_TOTAL_DATA_PATH`로 오버라이드 가능)
- 포트: 5000 (변경 시 app.py 조정)
- 정적 자산 캐싱 우회: `.env`의 `ASSET_VERSION` 값이 CSS/JS 요청에 `?v=`로 붙음

## 주요 경로
- `/` : 검색 메인 (sap-screen 기반 UI)
- `/order/<order_no>` : 오더 상세 + Excel 다운로드
- `/dashboard/` : 대시보드 메인 (전체 데이터)
- `/dashboard/<view>` : 전기/기계/장치/계기 하위 뷰 (`electric`, `mechanical`, `instrument`, `meter`)

## 디렉터리 구조 (핵심)
- `app/__init__.py` : Flask 팩토리, 블루프린트 등록
- `app/routes/search.py` : 검색/상세/Excel export 라우트 (검색 담당)
- `app/routes/dashboard.py` : 대시보드 라우트(메인+하위 뷰) (대시보드 담당)
- `app/services/data_store.py` : sap-screen 데이터 로딩/정규화/필터링
- `app/services/data_loader.py` : total_data.csv 로더
- `app/services/dashboard_data.py` : 대시보드 집계 로직(공통)
- `templates/layout.html` : 공통 레이아웃/사이드바
- `templates/search/` : 검색 뷰/오더 상세
- `templates/dashboard/` : 대시보드 템플릿
- `static/css` : 공통/검색/대시보드/오더 상세 스타일
- `static/js` : 검색 모달/버튼 로직, 대시보드 Chart.js 렌더
- `data/total_data.csv` : 기본 데이터(공용)

## 검색 기능 (sap-screen 이식)
- 다중 필터: Order No, Equipment No/명, 호기(Top), 작업반(Middle), 설비종류(Sub), 첨부 존재, 자재/작업자 추가 검색
- 결과: 테이블 + 상세 모달(정비 Long Text, 링크, 자재, 작업 정보)
- 오더 상세: `/order/<order_no>`에서 필드/자재/작업/Long Text 확인, Excel export 제공
- 데이터 소스: DataStore가 recent/legacy CSV를 정규화(기본은 공용 total_data.csv로 매핑)

## 대시보드 기능 (sap-dashboard 리팩터/통합)
- 뷰: 메인 `/dashboard/` + 하위 `/dashboard/<view>` (electric/mechanical/instrument/meter)
- 차트(공통 8종):
  1) 월간 건수 추이 (호기/반)
  2) Damage 유형 추이
  3) 호기별 파이 (Cost Center)
  4) 작업반 파이
  5) 월별 비용(전체/인건비/자재/기타)
  6) 작업반별 Actual Work
  7) Equipment별 Damage 스택 (TOP N)
  8) 호기별 상태(완료/진행) 스택
- 데이터 집계: `dashboard_data.py`에서 전처리/집계 후 Chart.js 데이터 포맷으로 전달
- 템플릿: `templates/dashboard/dashboard.html` 단일 템플릿에서 다중 캔버스 렌더

## 데이터 경로/환경변수
- 기본 공용 파일: `data/total_data.csv`
- `SAP_TOTAL_DATA_PATH` : 공용 파일 오버라이드
- `SAP_SCREEN_RECENT_PATH`, `SAP_SCREEN_LEGACY_PATH`, `SAP_SCREEN_DIR` : 검색 데이터 개별 지정 가능(기본은 공용 파일)
- `SAP_DASHBOARD_TOTAL_DATA` : 대시보드 전용 파일 지정(기본은 공용 파일)

## 네비게이션/레이아웃
- 공통 사이드바: 검색 ↔ 대시보드(메인+하위) 이동. 템플릿 매크로 `templates/components/sidebar.html` 사용, 접힘 상태는 `static/js/layout.js`로 localStorage에 저장.
- 테마: shadcn-like 스타일(Zinc/Slate 테마, 깔끔한 UI, primary #18181b).

## 담당 구분
- 검색 담당: `app/routes/search.py`, `templates/search/*`, `app/services/data_store.py`
- 대시보드 담당: `app/routes/dashboard.py`, `templates/dashboard/*`, `app/services/dashboard_data.py`, `app/services/data_loader.py`

## 테스트 현황
- 기본 경로 200 OK 확인: `/`, `/order/5012796`, `/dashboard/`, `/dashboard/{electric,mechanical,meter,instrument}` (test_client)
