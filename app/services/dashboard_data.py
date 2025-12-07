import pandas as pd
from typing import Dict, List, Any

BASE_COLORS = [
    "rgb(37, 99, 235)",
    "rgb(14, 165, 233)",
    "rgb(99, 102, 241)",
    "rgb(34, 197, 94)",
    "rgb(248, 113, 113)",
    "rgb(251, 146, 60)",
    "rgb(14, 116, 144)",
    "rgb(59, 130, 246)",
    "rgb(14, 165, 177)",
    "rgb(88, 28, 135)",
]


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Start of Execution이 공란이면 Bsc start 값을 사용
    # format='mixed'로 다양한 날짜 형식 처리 (YYYY-MM-DD, YYYY-MM-DD HH:MM:SS 등)
    df["Start of Execution"] = pd.to_datetime(df["Start of Execution"], format="mixed", errors="coerce")
    df["Bsc start"] = pd.to_datetime(df["Bsc start"], format="mixed", errors="coerce")
    df["실행일"] = df["Start of Execution"].fillna(df["Bsc start"])
    df = df.dropna(subset=["실행일"])
    df["년월"] = df["실행일"].dt.to_period("M").astype(str)
    df["Order No"] = df["Order No"].astype(str)

    numeric_cols = ["Total Cost", "Labor Cost", "Material Cost", "Other Cost", "Actual Work"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def group_cost_center(text: str) -> str:
    if pd.isna(text):
        return ""
    t = str(text)
    if any(k in t for k in ["발전BCP공통(5~6)", "발전CBP공통(5~6)", "인천복합발전5호기", "인천복합발전6호기"]):
        return "복합 5~6호기"
    if any(k in t for k in ["발전BCP공통(7~9)", "발전CBP공통(7~9)", "인천복합발전7호기", "인천복합발전8호기", "인천복합발전9호기"]):
        return "복합 7~9호기"
    if any(k in t for k in ["발전CBP공통(1~4)", "인천복합발전3호기_CBP", "인천복합발전4호기_CBP"]):
        return "복합 3~4호기"
    if "발전인천호기공통DUMMY" in t:
        return "발전호기 공통"
    return t


def group_work_center(text: str) -> str:
    if pd.isna(text):
        return ""
    t = str(text).strip()
    if t in ["계기반", "합자회사 동화-계기"]:
        return "계기"
    if t in ["전기반", "합자회사 동화-전기"]:
        return "전기"
    if t in ["기계반", "수산인더스트리-기계"]:
        return "기계"
    if t in ["장치반", "수산인더스트리-영선", "수산인더스트리-장치", "QSS 개선리더반"]:
        return "장치"
    if t in ["진단파트", "계획파트"]:
        return "진단"
    return t


def group_damage(text: str) -> str:
    if pd.isna(text):
        return ""
    text_upper = str(text).upper()
    if any(keyword in text_upper for keyword in ["LEAK", "CRACK", "PASSING"]):
        return "Leak&Passing"
    if text in ["고착", "마모"]:
        return "고착&마모"
    if text in ["변색", "변형"]:
        return "변색&변형"
    if text in ["부식", "소손"]:
        return "부식&소손"
    if text in [
        "CONTROL 불량",
        "Program Error",
        "Short",
        "간섭",
        "과열/발열",
        "끼임",
        "동파",
        "연소불량",
        "열화손상",
        "오염",
        "용단",
        "이완/이탈",
        "출력저하",
        "침수",
        "팽창",
    ]:
        return "기타"
    return text


def _chart(labels: List[str], series: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"labels": labels, "datasets": series}


def trend_by_cost_center(df: pd.DataFrame) -> Dict[str, Any]:
    temp = df.copy()
    temp["Grouped Cost Center"] = temp["Cost Center Text"].apply(group_cost_center)

    # Filter to show only specific cost centers
    allowed_centers = ["복합 3~4호기", "복합 5~6호기", "복합 7~9호기"]
    temp = temp[temp["Grouped Cost Center"].isin(allowed_centers)]

    grouped = temp.groupby(["년월", "Grouped Cost Center"])["Order No"].count().reset_index()
    labels = sorted(grouped["년월"].unique())
    centers = sorted([c for c in grouped["Grouped Cost Center"].unique() if c])
    datasets = []
    for idx, center in enumerate(centers):
        sub = grouped[grouped["Grouped Cost Center"] == center]
        data = [int(dict(zip(sub["년월"], sub["Order No"])) .get(m, 0)) for m in labels]
        color = BASE_COLORS[idx % len(BASE_COLORS)]
        datasets.append(
            {
                "label": center,
                "data": data,
                "borderColor": color,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.12)"),
                "tension": 0.1,
            }
        )
    return _chart(labels, datasets)


def damage_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """기간별 정비실적 - 월별 Order No 건수합"""
    temp = df.copy()
    # Order No 기준 중복 제거하여 고유 건수 계산
    temp = temp.drop_duplicates(subset=["Order No"])
    grouped = temp.groupby("년월")["Order No"].count().reset_index()
    grouped = grouped.sort_values("년월")
    labels = grouped["년월"].tolist()
    data = grouped["Order No"].astype(int).tolist()
    # 파란색 계열
    datasets = [
        {
            "label": "정비실적 건수",
            "data": data,
            "borderColor": "rgb(59, 130, 246)",
            "backgroundColor": "rgba(59, 130, 246, 0.7)",
        }
    ]
    return _chart(labels, datasets)


def cost_center_pie(df: pd.DataFrame) -> Dict[str, Any]:
    # Apply cost center grouping
    df = df.copy()
    df["Grouped Cost Center"] = df["Cost Center Text"].apply(group_cost_center)

    # Exclude specific cost centers
    exclude_centers = ["예방정비섹션", "계전섹션", "교육·지원섹션", "기계섹션"]
    df = df[~df["Grouped Cost Center"].isin(exclude_centers)]

    # Group by the grouped cost center
    grouped = df.groupby("Grouped Cost Center")["Order No"].count().reset_index()
    grouped = grouped[grouped["Grouped Cost Center"].notna()].sort_values("Order No", ascending=False)
    labels = grouped["Grouped Cost Center"].tolist()
    data = grouped["Order No"].astype(int).tolist()
    colors = [BASE_COLORS[i % len(BASE_COLORS)].replace("rgb", "rgba").replace(")", ", 0.8)") for i in range(len(labels))]
    return _chart(labels, [{"data": data, "backgroundColor": colors}])


def workctr_pie(df: pd.DataFrame) -> Dict[str, Any]:
    df = df.copy()
    df["Grouped Work Center"] = df["WorkCtr.Text"].apply(group_work_center)
    grouped = df.groupby("Grouped Work Center")["Order No"].count().reset_index()
    grouped = grouped[grouped["Grouped Work Center"].notna() & (grouped["Grouped Work Center"] != "")].sort_values("Order No", ascending=False)
    labels = grouped["Grouped Work Center"].tolist()
    data = grouped["Order No"].astype(int).tolist()
    colors = [BASE_COLORS[i % len(BASE_COLORS)].replace("rgb", "rgba").replace(")", ", 0.8)") for i in range(len(labels))]
    return _chart(labels, [{"data": data, "backgroundColor": colors}])


def cost_monthly(df: pd.DataFrame) -> Dict[str, Any]:
    if not {"Total Cost", "Labor Cost", "Material Cost", "Other Cost"}.issubset(df.columns):
        return _chart([], [])
    grouped = df.groupby("년월")[["Total Cost", "Labor Cost", "Material Cost", "Other Cost"]].sum().reset_index()
    grouped = grouped.sort_values("년월")
    labels = grouped["년월"].tolist()
    series_info = [
        ("Total Cost", "전체비용", "rgb(54, 162, 235)"),
        ("Labor Cost", "인건비", "rgb(255, 99, 132)"),
        ("Material Cost", "자재비", "rgb(75, 192, 192)"),
        ("Other Cost", "기타비용", "rgb(255, 159, 64)"),
    ]
    datasets = []
    for col, label, color in series_info:
        data = grouped[col].astype(float).round(0).tolist()
        datasets.append(
            {
                "label": label,
                "data": data,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.7)"),
                "borderColor": color,
                "borderWidth": 2,
                "fill": True,
                "tension": 0.1,
            }
        )
    return _chart(labels, datasets)


def cost_monthly_filtered(df: pd.DataFrame, cost_type: str = "Total Cost") -> Dict[str, Any]:
    """월별 비용 추이 - 선택한 비용 유형만 표시

    Args:
        df: 데이터프레임
        cost_type: 비용 유형 (Total Cost, Labor Cost, Material Cost, Other Cost)

    Returns:
        Chart.js 형식 데이터
    """
    cost_labels = {
        "Total Cost": ("전체비용", "rgb(54, 162, 235)"),
        "Labor Cost": ("인건비", "rgb(255, 99, 132)"),
        "Material Cost": ("자재비", "rgb(75, 192, 192)"),
        "Other Cost": ("기타비용", "rgb(255, 159, 64)"),
    }

    if cost_type not in df.columns:
        return _chart([], [])

    grouped = df.groupby("년월")[cost_type].sum().reset_index()
    grouped = grouped.sort_values("년월")
    labels = grouped["년월"].tolist()
    data = grouped[cost_type].astype(float).round(0).tolist()

    label_text, color = cost_labels.get(cost_type, (cost_type, "rgb(128, 128, 128)"))

    datasets = [{
        "label": label_text,
        "data": data,
        "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.7)"),
        "borderColor": color,
        "borderWidth": 2,
    }]

    return _chart(labels, datasets)


def workctr_time(df: pd.DataFrame) -> Dict[str, Any]:
    df = df.copy()
    df["Grouped Work Center"] = df["WorkCtr.Text"].apply(group_work_center)
    # Order No 기준 건수 (중복 제거)
    grouped = df.groupby("Grouped Work Center")["Order No"].nunique().reset_index()
    grouped.columns = ["Grouped Work Center", "count"]
    grouped = grouped[grouped["Grouped Work Center"].notna() & (grouped["Grouped Work Center"] != "")].sort_values("count", ascending=False)
    labels = grouped["Grouped Work Center"].tolist()
    data = grouped["count"].astype(int).tolist()
    colors = [BASE_COLORS[i % len(BASE_COLORS)].replace("rgb", "rgba").replace(")", ", 0.8)") for i in range(len(labels))]
    return _chart(labels, [{"data": data, "backgroundColor": colors}])


def equipment_damage(df: pd.DataFrame, top_n: int = 8) -> Dict[str, Any]:
    temp = df.copy()
    temp["Grouped Damage"] = temp["Damage"].apply(group_damage)
    grouped = temp.groupby(["Equipment", "Grouped Damage"])["Order No"].count().reset_index()
    top_equipment = grouped.groupby("Equipment")["Order No"].sum().nlargest(top_n).index.tolist()
    grouped = grouped[grouped["Equipment"].isin(top_equipment)]
    labels = sorted(grouped["Equipment"].unique())
    damages = sorted([d for d in grouped["Grouped Damage"].unique() if d])
    datasets = []
    for idx, dmg in enumerate(damages):
        sub = grouped[grouped["Grouped Damage"] == dmg]
        data_dict = dict(zip(sub["Equipment"], sub["Order No"]))
        data = [int(data_dict.get(eq, 0)) for eq in labels]
        color = BASE_COLORS[idx % len(BASE_COLORS)]
        datasets.append(
            {
                "label": dmg,
                "data": data,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.65)"),
                "borderColor": color,
                "borderWidth": 1,
            }
        )
    return _chart(labels, datasets)


def equipment_damage_by_month(df: pd.DataFrame, equipment: str = "") -> Dict[str, Any]:
    """Equipment 검색 필터 적용 (정확히 일치), X축을 년월로 표시, Damage별 누적 막대그래프"""
    temp = df.copy()
    temp["Grouped Damage"] = temp["Damage"].apply(group_damage)

    # Equipment 컬럼을 문자열로 변환 (float -> str, 소수점 제거)
    temp["Equipment"] = temp["Equipment"].apply(
        lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() else str(x) if pd.notna(x) else ""
    )

    # Equipment 필터 적용 (정확히 일치)
    if equipment:
        temp = temp[temp["Equipment"] == equipment.strip()]

    if temp.empty:
        return _chart([], [])

    # 년월별, Damage별 Order No 건수 집계 (중복 제거)
    grouped = temp.groupby(["년월", "Grouped Damage"])["Order No"].nunique().reset_index()
    grouped.columns = ["년월", "Grouped Damage", "count"]

    # X축 레이블을 "년 월" 형식으로 변환
    sorted_months = sorted(grouped["년월"].unique())
    labels = [f"{ym[:4]}년 {ym[5:]}월" for ym in sorted_months]
    damages = sorted([d for d in grouped["Grouped Damage"].unique() if d])

    datasets = []
    for idx, dmg in enumerate(damages):
        sub = grouped[grouped["Grouped Damage"] == dmg]
        data_dict = dict(zip(sub["년월"], sub["count"]))
        data = [int(data_dict.get(ym, 0)) for ym in sorted_months]
        color = BASE_COLORS[idx % len(BASE_COLORS)]
        datasets.append(
            {
                "label": dmg,
                "data": data,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.65)"),
                "borderColor": color,
                "borderWidth": 1,
            }
        )
    return _chart(labels, datasets)


def status_by_cost_center(df: pd.DataFrame) -> Dict[str, Any]:
    temp = df.copy()
    def group_status(status):
        if pd.isna(status):
            return "진행중"
        s = str(status).strip().upper()
        if s in ["CLOSED", "COMPLETE", "CONFIRM", "CNF", "CLOS", "COMP"]:
            return "완료"
        return "진행중"

    temp["Grouped Cost Center"] = temp["Cost Center Text"].apply(group_cost_center)
    temp["Grouped Status"] = temp["Order Status"].apply(group_status)
    # Order No 기준 중복 제거
    grouped = temp.groupby(["Grouped Cost Center", "Grouped Status"])["Order No"].nunique().reset_index()

    # 지정된 4개 호기만 지정된 순서로 표시
    allowed_centers = ["복합 3~4호기", "복합 5~6호기", "복합 7~9호기", "발전호기 공통"]
    centers = [c for c in allowed_centers if c in grouped["Grouped Cost Center"].unique()]

    # 진행중(왼쪽), 완료(오른쪽) 순서
    statuses = ["진행중", "완료"]
    status_colors = {
        "진행중": "rgb(251, 146, 60)",  # 주황색
        "완료": "rgb(34, 197, 94)",      # 녹색
    }
    labels = centers
    datasets = []
    for status in statuses:
        sub = grouped[grouped["Grouped Status"] == status]
        data_dict = dict(zip(sub["Grouped Cost Center"], sub["Order No"]))
        data = [int(data_dict.get(c, 0)) for c in centers]
        color = status_colors[status]
        datasets.append(
            {
                "label": status,
                "data": data,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.7)"),
                "borderColor": color,
            }
        )
    return _chart(labels, datasets)


def workctr_order_and_work_comparison(df: pd.DataFrame, workctrs: List[str], label_map: Dict[str, str] = None) -> Dict[str, Any]:
    """직영/상주 Order 건수 및 Actual Work 비교 - 이중 도넛 차트용 데이터

    Args:
        df: 데이터프레임
        workctrs: 비교할 WorkCtr.Text 목록 (예: ['전기반', '합자회사 동화-전기'])
        label_map: 레이블 변환 맵 (예: {'합자회사 동화-전기': '동화(전기)'})

    Returns:
        order_count: Order 건수 도넛 데이터
        actual_work: Actual Work 합계 도넛 데이터
    """
    if label_map is None:
        label_map = {}

    temp = df.copy()
    # 해당 WorkCtr만 필터링
    temp = temp[temp["WorkCtr.Text"].isin(workctrs)]

    if temp.empty:
        return {
            "order_count": _chart([], []),
            "actual_work": _chart([], [])
        }

    # Order 건수 (중복 제거)
    order_grouped = temp.groupby("WorkCtr.Text")["Order No"].nunique().reset_index()
    order_grouped.columns = ["WorkCtr.Text", "count"]

    # Actual Work 합계
    work_grouped = temp.groupby("WorkCtr.Text")["Actual Work"].sum().reset_index()
    work_grouped.columns = ["WorkCtr.Text", "work"]

    # 직영/상주 레이블 매핑 (직영: 외주업체, 상주: 자체반)
    # 전기반 = 상주, 합자회사 동화-전기 = 직영
    direct_label_map = {
        "전기반": "상주",
        "합자회사 동화-전기": "직영",
        "기계반": "상주",
        "수산인더스트리-기계": "직영",
        "장치반": "상주",
        "수산인더스트리-장치": "직영",
        "수산인더스트리-영선": "직영",
        "계기반": "상주",
        "합자회사 동화-계기": "직영",
    }

    # 레이블 생성 (workctrs 순서 유지)
    labels = []
    order_data = []
    work_data = []

    for wc in workctrs:
        # 직영/상주 레이블 사용
        label = direct_label_map.get(wc, label_map.get(wc, wc))
        labels.append(label)

        order_row = order_grouped[order_grouped["WorkCtr.Text"] == wc]
        order_data.append(int(order_row["count"].values[0]) if len(order_row) > 0 else 0)

        work_row = work_grouped[work_grouped["WorkCtr.Text"] == wc]
        work_data.append(round(float(work_row["work"].values[0]), 1) if len(work_row) > 0 else 0)

    # 색상 설정 (상주: 파란색, 직영: 녹색)
    color_map = {
        "상주": "rgba(37, 99, 235, 0.8)",   # 파란색
        "직영": "rgba(34, 197, 94, 0.8)",   # 녹색
    }
    colors = [color_map.get(label, "rgba(128, 128, 128, 0.8)") for label in labels]

    return {
        "order_count": _chart(labels, [{"data": order_data, "backgroundColor": colors}]),
        "actual_work": _chart(labels, [{"data": work_data, "backgroundColor": colors}])
    }


def cost_by_cost_center(df: pd.DataFrame, cost_type: str = "Total Cost") -> Dict[str, Any]:
    """호기별 정비비용 - X축: 년월, Y축: 비용, 범례: 호기별

    Args:
        df: 데이터프레임
        cost_type: 비용 유형 (Total Cost, Labor Cost, Material Cost, Other Cost)

    Returns:
        Chart.js 형식 데이터
    """
    temp = df.copy()
    temp["Grouped Cost Center"] = temp["Cost Center Text"].apply(group_cost_center)

    # 지정된 호기만 필터링
    allowed_centers = ["복합 3~4호기", "복합 5~6호기", "복합 7~9호기"]
    temp = temp[temp["Grouped Cost Center"].isin(allowed_centers)]

    if temp.empty or cost_type not in temp.columns:
        return _chart([], [])

    # 년월별, 호기별 비용 합계
    grouped = temp.groupby(["년월", "Grouped Cost Center"])[cost_type].sum().reset_index()
    grouped = grouped.sort_values("년월")

    # X축 레이블 (년월)
    sorted_months = sorted(grouped["년월"].unique())
    labels = sorted_months

    # 호기별 데이터셋 생성
    center_colors = {
        "복합 3~4호기": "rgb(37, 99, 235)",    # 파란색
        "복합 5~6호기": "rgb(34, 197, 94)",    # 녹색
        "복합 7~9호기": "rgb(251, 146, 60)",   # 주황색
    }

    datasets = []
    for center in allowed_centers:
        sub = grouped[grouped["Grouped Cost Center"] == center]
        data_dict = dict(zip(sub["년월"], sub[cost_type]))
        data = [round(float(data_dict.get(ym, 0)), 0) for ym in sorted_months]
        color = center_colors.get(center, BASE_COLORS[0])
        datasets.append({
            "label": center,
            "data": data,
            "borderColor": color,
            "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.2)"),
            "borderWidth": 2,
            "fill": False,
            "tension": 0.1,
        })

    return _chart(labels, datasets)


def get_raw_data(df: pd.DataFrame) -> Dict[str, Any]:
    """필터링을 위한 원본 데이터 반환"""
    temp = df.copy()
    temp["Grouped Cost Center"] = temp["Cost Center Text"].apply(group_cost_center)
    temp["Grouped Damage"] = temp["Damage"].apply(group_damage)

    return {
        "trend": temp[["년월", "Cost Center Text", "Grouped Cost Center", "Order No"]].to_dict("records"),
        "damage_trend": temp[["년월", "Damage", "Grouped Damage", "Order No"]].to_dict("records"),
        "cost_center_pie": temp[["년월", "Cost Center Text", "Order No"]].to_dict("records"),
        "workctr_pie": temp[["년월", "WorkCtr.Text", "Order No"]].to_dict("records"),
        "cost_chart": temp[["년월", "Total Cost", "Labor Cost", "Material Cost", "Other Cost", "Order No"]].to_dict("records"),
        "workctr_time": temp[["년월", "WorkCtr.Text", "Actual Work", "Order No"]].to_dict("records"),
        "equipment_damage": temp[["년월", "Equipment", "Damage", "Grouped Damage", "Order No"]].to_dict("records"),
        "status_by_cost": temp[["년월", "Cost Center Text", "Grouped Cost Center", "Order Status", "Order No"]].to_dict("records"),
    }


def get_filter_options(df: pd.DataFrame) -> Dict[str, Any]:
    """필터링 옵션 반환"""
    temp = df.copy()
    temp["Grouped Cost Center"] = temp["Cost Center Text"].apply(group_cost_center)

    # Filter to show only specific cost centers in filter options
    allowed_centers = ["복합 3~4호기", "복합 5~6호기", "복합 7~9호기"]
    filtered_centers = [c for c in temp["Grouped Cost Center"].unique() if c in allowed_centers]

    all_months = sorted(temp["년월"].unique().tolist())

    return {
        "cost_centers": sorted(filtered_centers),
        "cost_centers_raw": sorted([c for c in temp["Cost Center Text"].dropna().unique() if c]),
        "workctrs": sorted([w for w in temp["WorkCtr.Text"].dropna().unique() if w]),
        "damages": sorted([d for d in temp["Damage"].dropna().unique() if d]),
        "equipments": sorted([e for e in temp["Equipment"].dropna().unique() if e]),
        "years": sorted(list(set([m[:4] for m in all_months]))),
        "months": [f"{i:02d}" for i in range(1, 13)],
        "min_month": all_months[0] if all_months else "",
        "max_month": all_months[-1] if all_months else "",
    }
