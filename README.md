# SAP Data Portal (검색 + 대시보드)

## 실행
- uv 기반 실행: `uv run python app.py`
- 기본 포트: 5000 → http://127.0.0.1:5000/
- 데이터 파일: 기본 `data/total_data.csv` (없으면 실행 시 오류)
- 정적 캐싱 우회: `.env`에 `ASSET_VERSION`을 두고 CSS/JS 요청에 `?v=`로 전달 (Cloudflare 캐시 무효화 시 숫자 변경)

## 주요 기능
- 검색(SAP Screen 이식)
  - 다중 필터: Order No, Equipment No/명, 호기/작업반/설비종류, 첨부 여부, 자재/작업자 추가 검색
  - 결과 테이블 + 상세 모달(정비 Long Text, 링크, 자재, 작업 정보)
  - 오더 상세 페이지: `/order/<order_no>` + Excel 다운로드
- 대시보드(SAP Dashboard 리팩터)
  - 메인 `/dashboard/` + 하위 `/dashboard/<view>` : electric, mechanical, instrument, meter
  - 차트 8종: 월간 건수, Damage 추이, 호기/작업반 파이, 월별 비용, 작업반 Actual Work, Equipment Damage 스택, 호기별 상태 스택
- 공통 테마/사이드바: 검색↔대시보드 이동, shadcn-like 스타일(Zinc/Slate 테마, 깔끔한 UI). 사이드바는 접기/펼치기 가능하며 상태는 로컬에 저장됨.
- 정적 자산: 공통/검색/대시보드 CSS와 JS를 `static/`에서 관리 (템플릿의 inline 스타일/스크립트 제거)

## 데이터/환경변수
- 기본 공용 파일: `data/total_data.csv`
- 오버라이드:
  - `SAP_TOTAL_DATA_PATH` : 공용 파일 경로
  - `SAP_SCREEN_RECENT_PATH`, `SAP_SCREEN_LEGACY_PATH`, `SAP_SCREEN_DIR` : 검색 데이터 개별 지정
  - `SAP_DASHBOARD_TOTAL_DATA` : 대시보드 전용 파일 지정

## 코드 구조
- `app/__init__.py` : Flask 팩토리, 블루프린트 등록
- `app/routes/search.py` : 검색/상세/Excel
- `app/routes/dashboard.py` : 대시보드 메인+하위 뷰
- `app/services/data_store.py` : 검색 데이터 로딩/정규화/필터
- `app/services/data_loader.py` : total_data 로더
- `app/services/dashboard_data.py` : 대시보드 집계(차트 데이터 포맷)
- `templates/layout.html` : 공통 레이아웃/사이드바
- `templates/search/*` : 검색/오더 상세
- `templates/dashboard/dashboard.html` : 대시보드(메인+하위 공용)
- `static/css` : 레이아웃/검색/대시보드/오더 상세 스타일
- `static/js` : 검색 모달/버튼 로직, 대시보드 Chart.js 렌더링
- `data/` : 기본 데이터 위치

## 테스트
- test_client로 200 OK 확인: `/`, `/order/5012796`, `/dashboard/`, `/dashboard/{electric,mechanical,meter,instrument}`

## 역할 분리 (개발자 협업)
- 검색 담당: `app/routes/search.py`, `templates/search/*`, `app/services/data_store.py`
- 대시보드 담당: `app/routes/dashboard.py`, `templates/dashboard/*`, `app/services/dashboard_data.py`, `app/services/data_loader.py`
