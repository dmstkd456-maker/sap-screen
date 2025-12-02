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
    df["Finish Execution"] = pd.to_datetime(df["Finish Execution"], errors="coerce")
    df = df.dropna(subset=["Finish Execution"])
    df["년월"] = df["Finish Execution"].dt.to_period("M").astype(str)
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
    temp = df.copy()
    temp["Grouped Damage"] = temp["Damage"].apply(group_damage)
    grouped = temp.groupby(["년월", "Grouped Damage"])["Order No"].count().reset_index()
    labels = sorted(grouped["년월"].unique())
    damages = sorted([d for d in grouped["Grouped Damage"].unique() if d])
    datasets = []
    for idx, dmg in enumerate(damages):
        sub = grouped[grouped["Grouped Damage"] == dmg]
        data = [int(dict(zip(sub["년월"], sub["Order No"])) .get(m, 0)) for m in labels]
        color = BASE_COLORS[idx % len(BASE_COLORS)]
        datasets.append(
            {
                "label": dmg,
                "data": data,
                "borderColor": color,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.2)"),
                "tension": 0.1,
            }
        )
    return _chart(labels, datasets)


def cost_center_pie(df: pd.DataFrame) -> Dict[str, Any]:
    grouped = df.groupby("Cost Center Text")["Order No"].count().reset_index()
    grouped = grouped[grouped["Cost Center Text"].notna()].sort_values("Order No", ascending=False)
    labels = grouped["Cost Center Text"].tolist()
    data = grouped["Order No"].astype(int).tolist()
    colors = [BASE_COLORS[i % len(BASE_COLORS)].replace("rgb", "rgba").replace(")", ", 0.8)") for i in range(len(labels))]
    return _chart(labels, [{"data": data, "backgroundColor": colors}])


def workctr_pie(df: pd.DataFrame) -> Dict[str, Any]:
    grouped = df.groupby("WorkCtr.Text")["Order No"].count().reset_index()
    grouped = grouped[grouped["WorkCtr.Text"].notna()].sort_values("Order No", ascending=False)
    labels = grouped["WorkCtr.Text"].tolist()
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
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.2)"),
                "borderColor": color,
                "borderWidth": 2,
                "fill": True,
                "tension": 0.1,
            }
        )
    return _chart(labels, datasets)


def workctr_time(df: pd.DataFrame) -> Dict[str, Any]:
    if "Actual Work" not in df.columns:
        return _chart([], [])
    grouped = df.groupby("WorkCtr.Text")["Actual Work"].sum().reset_index()
    grouped = grouped[grouped["WorkCtr.Text"].notna()].sort_values("Actual Work", ascending=False)
    labels = grouped["WorkCtr.Text"].tolist()
    data = grouped["Actual Work"].astype(float).round(1).tolist()
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
    grouped = temp.groupby(["Grouped Cost Center", "Grouped Status"])["Order No"].count().reset_index()
    centers = sorted([c for c in grouped["Grouped Cost Center"].unique() if c])
    statuses = ["완료", "진행중"]
    labels = centers
    datasets = []
    for idx, status in enumerate(statuses):
        sub = grouped[grouped["Grouped Status"] == status]
        data_dict = dict(zip(sub["Grouped Cost Center"], sub["Order No"]))
        data = [int(data_dict.get(c, 0)) for c in centers]
        color = BASE_COLORS[idx % len(BASE_COLORS)]
        datasets.append(
            {
                "label": status,
                "data": data,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.7)"),
                "borderColor": color,
            }
        )
    return _chart(labels, datasets)
