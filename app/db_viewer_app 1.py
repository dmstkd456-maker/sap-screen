import sqlite3
import pandas as pd
import re
import os
from flask import Flask, render_template, jsonify, request

# 공통 설정 모듈 임포트
from config import DB_PATH, TABLE_NAME, LOG_TABLE_NAME

# Flask 애플리케이션 생성 - 템플릿 폴더를 상위 디렉토리의 templates로 설정
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

def get_datatables_data(conn, query):
    """
    데이터베이스에서 데이터를 읽고 DataTables가 요구하는 형식으로 변환합니다.
    컬럼 이름을 원본(title)과 JS 호환(data) 버전으로 분리하여 반환합니다.
    """
    df = pd.read_sql_query(query, conn)
    df.fillna('', inplace=True)
    
    original_columns = df.columns.tolist()
    sanitized_columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col) for col in original_columns]
    
    # DataTables에 전달할 컬럼 정의
    dt_columns = [{'title': orig, 'data': san} for orig, san in zip(original_columns, sanitized_columns)]
    
    # to_dict()를 위해 DataFrame의 컬럼 이름을 변경
    df.columns = sanitized_columns
    
    data = df.to_dict(orient='records')
    
    return {'columns': dt_columns, 'data': data}

# --- Main Page --- 
@app.route('/')
def index():
    """메인 데이터 뷰어 페이지를 렌더링합니다."""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """메인 데이터를 JSON으로 반환합니다 (서버사이드 페이지네이션 지원)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # DataTables 서버사이드 파라미터
            draw = request.args.get('draw', type=int, default=1)
            start = request.args.get('start', type=int, default=0)
            length = request.args.get('length', type=int, default=100)
            search_value = request.args.get('search[value]', default='')
            order_column_idx = request.args.get('order[0][column]', type=int, default=0)
            order_dir = request.args.get('order[0][dir]', default='asc')
            show_updated_only = request.args.get('show_updated_only', default='false') == 'true'

            # 컬럼 정보 가져오기
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
            columns_info = cursor.fetchall()
            original_columns = [col[1] for col in columns_info]
            sanitized_columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col) for col in original_columns]
            dt_columns = [{'title': orig, 'data': san} for orig, san in zip(original_columns, sanitized_columns)]

            # 전체 레코드 수
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_records = cursor.fetchone()[0]

            # WHERE 절 구성
            where_clauses = []
            params = []

            # 업데이트된 항목만 필터
            if show_updated_only and 'last_updated' in original_columns:
                where_clauses.append("last_updated IS NOT NULL AND last_updated != ''")

            # 검색 필터
            if search_value:
                search_conditions = []
                for col in original_columns:
                    search_conditions.append(f'"{col}" LIKE ?')
                    params.append(f'%{search_value}%')
                where_clauses.append(f"({' OR '.join(search_conditions)})")

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # 필터된 레코드 수
            count_query = f"SELECT COUNT(*) FROM {TABLE_NAME} {where_sql}"
            cursor.execute(count_query, params)
            filtered_records = cursor.fetchone()[0]

            # 정렬
            order_column = original_columns[order_column_idx] if order_column_idx < len(original_columns) else original_columns[0]
            order_sql = f'ORDER BY "{order_column}" {order_dir.upper()}'

            # 페이지네이션된 데이터 가져오기
            if length == -1:  # 모두 보기
                data_query = f'SELECT * FROM {TABLE_NAME} {where_sql} {order_sql}'
                df = pd.read_sql_query(data_query, conn, params=params)
            else:
                data_query = f'SELECT * FROM {TABLE_NAME} {where_sql} {order_sql} LIMIT ? OFFSET ?'
                df = pd.read_sql_query(data_query, conn, params=params + [length, start])

            df.fillna('', inplace=True)
            df.columns = sanitized_columns
            data = df.to_dict(orient='records')

            return jsonify({
                'draw': draw,
                'recordsTotal': total_records,
                'recordsFiltered': filtered_records,
                'columns': dt_columns,
                'data': data
            })
    except Exception as e:
        print(f"메인 데이터 API 오류: {e}")
        return jsonify({'error': str(e)}), 500

# --- Log Page ---
@app.route('/log')
def log_page():
    """업데이트 로그 뷰어 페이지를 렌더링합니다."""
    return render_template('log.html')

@app.route('/api/log_data')
def get_log_data():
    """업데이트 로그 데이터를 JSON으로 반환합니다."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            response_data = get_datatables_data(conn, f"SELECT * FROM {LOG_TABLE_NAME}")
            return jsonify(response_data)
    except Exception as e:
        print(f"로그 데이터 API 오류: {e}")
        return jsonify({'error': str(e)}), 500

# --- Dashboard Page ---
@app.route('/dashboard')
def dashboard_page():
    """정비 통계 대시보드 페이지를 렌더링합니다."""
    return render_template('dashboard.html')

@app.route('/api/dashboard_stats')
def get_dashboard_stats():
    """대시보드용 통계 데이터를 JSON으로 반환합니다."""
    try:
        # 날짜 필터 파라미터 가져오기
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        with sqlite3.connect(DB_PATH) as conn:
            # 기계반(Planner grop = 110)만 필터링
            base_filter = 'WHERE "Planner grop" = \'110\''

            # 날짜 필터 추가
            if start_date and end_date:
                base_filter += f' AND date("Bsc start") BETWEEN \'{start_date}\' AND \'{end_date}\''

            # 1. 설비 타입별 정비 건수 TOP 10
            equipment_type_query = f'''
                SELECT "Equipment Type", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Equipment Type" != ""
                GROUP BY "Equipment Type"
                ORDER BY count DESC
                LIMIT 10
            '''
            equipment_type_df = pd.read_sql_query(equipment_type_query, conn)

            # 설비 타입별 상세 정보 (클릭용)
            equipment_type_details = {}
            for eq_type in equipment_type_df['Equipment Type']:
                detail_query = f'''
                    SELECT "Object type text", COUNT(*) as count
                    FROM {TABLE_NAME}
                    {base_filter} AND "Equipment Type" = '{eq_type}' AND "Object type text" != ""
                    GROUP BY "Object type text"
                    ORDER BY count DESC
                    LIMIT 5
                '''
                detail_df = pd.read_sql_query(detail_query, conn)
                equipment_type_details[eq_type] = detail_df.to_dict('records')

            # 2. 설비별 정비 건수 TOP 10
            equipment_query = f'''
                SELECT "Equi. Text", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Equi. Text" != ""
                GROUP BY "Equi. Text"
                ORDER BY count DESC
                LIMIT 10
            '''
            equipment_df = pd.read_sql_query(equipment_query, conn)

            # 3. 부품 사용량 TOP 20 (Material 컬럼 기준)
            material_query = f'''
                SELECT "Material", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Material" != ""
                GROUP BY "Material"
                ORDER BY count DESC
                LIMIT 20
            '''
            material_df = pd.read_sql_query(material_query, conn)

            # 4. 연도별 작업 TOP 5 (Order No 기준 중복 제거, Equi. Text 기준)
            yearly_work_query = f'''
                SELECT
                    strftime('%Y', "Bsc start") as year,
                    "Equi. Text",
                    COUNT(DISTINCT "Order No") as count
                FROM {TABLE_NAME}
                {base_filter} AND "Bsc start" != "" AND "Equi. Text" != ""
                GROUP BY year, "Equi. Text"
                ORDER BY year DESC, count DESC
            '''
            yearly_work_df = pd.read_sql_query(yearly_work_query, conn)

            # 연도별 TOP 5 필터링
            yearly_top5 = {}
            for year in yearly_work_df['year'].unique():
                if year and year != 'None':
                    year_data = yearly_work_df[yearly_work_df['year'] == year].head(5)
                    yearly_top5[year] = year_data[['Equi. Text', 'count']].to_dict('records')

            # 5. 월별 정비 건수 (최근 24개월)
            monthly_query = f'''
                SELECT
                    strftime('%Y-%m', "Bsc start") as month,
                    COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Bsc start" != ""
                GROUP BY month
                ORDER BY month DESC
                LIMIT 24
            '''
            monthly_df = pd.read_sql_query(monthly_query, conn)
            monthly_df = monthly_df.sort_values('month')  # 오름차순 정렬

            # 6. 작업 상태 분포
            status_query = f'''
                SELECT "Order Status", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Order Status" != ""
                GROUP BY "Order Status"
                ORDER BY count DESC
            '''
            status_df = pd.read_sql_query(status_query, conn)

            # 7. 정비 유형 분포
            order_type_query = f'''
                SELECT "Order Type Text", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Order Type Text" != ""
                GROUP BY "Order Type Text"
                ORDER BY count DESC
            '''
            order_type_df = pd.read_sql_query(order_type_query, conn)

            # 8. 위치별 정비 건수 (C/C를 CC로 통합)
            location_query = f'''
                SELECT "Loc. Text", COUNT(*) as count
                FROM {TABLE_NAME}
                {base_filter} AND "Loc. Text" != ""
                GROUP BY "Loc. Text"
                ORDER BY count DESC
            '''
            location_df = pd.read_sql_query(location_query, conn)

            # C/C를 CC로 통합
            location_df['Loc. Text'] = location_df['Loc. Text'].replace({
                'C/C #3': 'CC#03,04 Common Plant',
                'C/C #4': 'CC#03,04 Common Plant',
                'C/C #5': 'CC#05,06 Common Plant',
                'C/C #6': 'CC#05,06 Common Plant',
                'C/C #7': 'CC#07,08,09 Common Plant',
                'C/C #8': 'CC#07,08,09 Common Plant',
                'C/C #9': 'CC#07,08,09 Common Plant'
            })
            location_df = location_df.groupby('Loc. Text')['count'].sum().reset_index()
            location_df = location_df.sort_values('count', ascending=False).head(10)

            # 9. 연도별 비교 (전체 기간)
            yearly_comparison_query = f'''
                SELECT
                    strftime('%Y', "Bsc start") as year,
                    COUNT(*) as count
                FROM {TABLE_NAME}
                WHERE "Planner grop" = '110' AND "Bsc start" != ""
                GROUP BY year
                ORDER BY year
            '''
            yearly_comparison_df = pd.read_sql_query(yearly_comparison_query, conn)

            # 10. 월별 평균 비교 (연도별)
            monthly_avg_query = f'''
                SELECT
                    strftime('%Y', "Bsc start") as year,
                    CAST(strftime('%m', "Bsc start") AS INTEGER) as month,
                    COUNT(*) as count
                FROM {TABLE_NAME}
                WHERE "Planner grop" = '110' AND "Bsc start" != ""
                GROUP BY year, month
                ORDER BY year, month
            '''
            monthly_avg_df = pd.read_sql_query(monthly_avg_query, conn)

            # 연도별로 월평균 계산
            monthly_avg_comparison = []
            for year in monthly_avg_df['year'].unique():
                if year and year != 'None':
                    year_data = monthly_avg_df[monthly_avg_df['year'] == year]
                    monthly_counts = [0] * 12
                    for _, row in year_data.iterrows():
                        if row['month']:
                            monthly_counts[int(row['month']) - 1] = row['count']
                    monthly_avg_comparison.append({
                        'year': year,
                        'monthly_avg': monthly_counts
                    })

            # 11. 연도별 설비 타입 트렌드
            yearly_equipment_trend_query = f'''
                SELECT
                    strftime('%Y', "Bsc start") as year,
                    "Equipment Type",
                    COUNT(*) as count
                FROM {TABLE_NAME}
                WHERE "Planner grop" = '110' AND "Bsc start" != "" AND "Equipment Type" != ""
                GROUP BY year, "Equipment Type"
                ORDER BY year, count DESC
            '''
            yearly_equipment_trend_df = pd.read_sql_query(yearly_equipment_trend_query, conn)

            # 연도별로 그룹화
            yearly_equipment_trend = []
            for year in yearly_equipment_trend_df['year'].unique():
                if year and year != 'None':
                    year_data = yearly_equipment_trend_df[yearly_equipment_trend_df['year'] == year]
                    equipment_types = []
                    for _, row in year_data.iterrows():
                        equipment_types.append({
                            'type': row['Equipment Type'],
                            'count': row['count']
                        })
                    yearly_equipment_trend.append({
                        'year': year,
                        'equipment_types': equipment_types
                    })

            # JSON 응답 구성
            return jsonify({
                'equipment_type': equipment_type_df.to_dict('records'),
                'equipment_type_details': equipment_type_details,
                'equipment': equipment_df.to_dict('records'),
                'material': material_df.to_dict('records'),
                'yearly_top5': yearly_top5,
                'monthly': monthly_df.to_dict('records'),
                'status': status_df.to_dict('records'),
                'order_type': order_type_df.to_dict('records'),
                'location': location_df.to_dict('records'),
                'yearly_comparison': yearly_comparison_df.to_dict('records'),
                'monthly_avg_comparison': monthly_avg_comparison,
                'yearly_equipment_trend': yearly_equipment_trend
            })
    except Exception as e:
        print(f"대시보드 통계 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=====================================================")
    print(" SAP 데이터베이스 뷰어")
    print("=====================================================")
    print(" 웹 서버가 시작되었습니다.")
    print(" 웹 브라우저를 열고 아래 주소로 접속하세요:")
    print("")
    print(" http://127.0.0.1:5000")
    print("")
    print(" 서버를 중지하려면 터미널에서 Ctrl+C 를 누르세요.")
    print("=====================================================")
    app.run(debug=True)