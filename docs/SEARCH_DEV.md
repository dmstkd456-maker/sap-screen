# 검색 개발자 가이드

## 소유 영역
- 라우트: `app/routes/search.py`
- 서비스: `app/services/data_store.py`
- 템플릿: `templates/search/index.html`, `templates/search/order_detail.html`
- 스타일: `static/css/search.css`, 공통 레이아웃 `static/css/layout.css`
- JS: `static/js/search.js` (모달/초기화/뒤로가기)
- 공통 레이아웃: `templates/layout.html` (사이드바 nav_active만 사용)
- 캐시 버전: `.env`의 `ASSET_VERSION`을 정적 자산 쿼리파라미터로 전달해 Cloudflare 캐싱 우회

## 데이터
- 기본 파일: `data/total_data.csv` (공용). 필요 시 env로 오버라이드:
  - `SAP_TOTAL_DATA_PATH`
  - `SAP_SCREEN_RECENT_PATH`, `SAP_SCREEN_LEGACY_PATH`, `SAP_SCREEN_DIR`
- DataStore가 recent/legacy 병합 후 정규화/필터링 제공. 필터/정규화 추가는 `data_store.py` 내부에서 처리.

## 실행/테스트
- 실행: `uv run python app.py`
- 샘플 검증: `/` , `/order/<id>` (예: `/order/5012796`)
- 테스트 데이터 존재 여부를 먼저 확인(파일 누락 시 빈 DF 반환).

## 변경 지침
- 필터 추가: `_apply_filters`에 조건 추가, 선택 UI는 `templates/search/index.html`에 필드/hidden 전달 동기화.
- 테이블/모달 필드 변경: `_build_table_rows`에서 데이터 구성 → 템플릿 컬럼 정의(`TABLE_COLUMNS`)와 일치시키기.
- 상세 페이지 필드: `ORDER_INFO_FIELDS`를 수정하면 `/order/<id>` 렌더에 반영.
- Excel export:
  - 단일 오더 (전체): `/order/<id>/export`가 DataFrame 그대로 저장
  - 단일 오더 (상세내역): `/order/<id>/export_detail`가 Order No, Order Short Text, Equipment, 설비명, 작업 정보, 자재 정보만 저장 (모달용)
  - 검색 결과: `/export`가 검색 조건 기반 전체 결과를 flatten하여 저장 (작업 정보, Long Text, 자재 포함)
  - 검색 결과 export는 `build_excel_export_data()`로 detail_payload를 펼쳐서 엑셀 컬럼으로 변환
  - 검색 결과 엑셀은 `insert_blank_rows_between_orders()`로 Order No가 바뀔 때마다 빈 행 삽입 (가독성 향상)
  - 엑셀 포맷팅: `format_excel_worksheet()`로 행 높이(25), 열 너비 자동 조정, 텍스트 줄바꿈 적용
  - Equipment 번호로 검색 시 파일명에 Equipment 번호 포함
- 정렬 우선순위: `_select_order_numbers()`에서 Order Short Text에 "도면정보" 포함된 오더를 최우선 정렬 (작업일자 무관)
- 작업일자: `Start of Execution` → `Bsc start` → 기타 날짜 컬럼 순으로 fallback (recent/legacy 구분 제거)
- 설비명 검색: Order Short Text와 Equi. Text 필드 모두 검색 (OR 조건). 특수문자(-, _, ", . 등)로 단어를 분리하고, 검색어의 모든 단어가 독립된 단어로 존재하는지 확인. 단어 순서 무관 (예: "slp c" 검색 시 "SLP-C", "SLP Screen C" 매칭, "SLP COUPLING"은 불일치 - C가 독립 단어 아님)
  - 양방향 용어 매핑: `data/unit_mappings.json`에서 한글↔영문 약어 매핑을 로드하여 검색 토큰 확장 (예: "펌프" 검색 시 "pump", "pp" 등도 매칭)
- 작업반 별칭: `MIDDLE_CATEGORY_ALIASES`로 여러 업체명을 하나의 작업반으로 통합 필터링 (예: "기계" 선택 시 "기계반", "수산인더스트리-기계" 모두 조회). 검색 결과 테이블에는 원본 작업반명(`WorkCtr.Text`) 그대로 표시.
- nav_active: 레이아웃 사이드바 활성화를 위해 `render_template(..., nav_active="search")` 유지.

## 코드 스타일
- pandas 전처리는 DataStore 내에서 수행, 라우트에서는 가급적 가공 최소화.
- 한글 컬럼/텍스트는 기존 방식 유지(UTF-8). 외부 입력은 `.strip()` 후 비교.
- 템플릿은 Jinja + 순수 JS. 모달/버튼 로직은 `static/js/search.js`, 스타일은 `static/css/search.css`에서 관리(템플릿 inline 사용 지양).

## 주의
- 원본 CSV 스키마가 변동될 수 있으므로 컬럼 사용 시 `in` 체크 후 기본값/빈 문자열 처리.
- 세션/스토리지 사용 없음. 모든 상태는 쿼리 파라미터 기반. 필요시 querystring 보존에 유의.
