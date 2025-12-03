from flask import Blueprint, abort, render_template

from app.services.data_loader import load_data
from app.services import dashboard_data as dd

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

VIEW_CONFIG = {
    "electric": {
        "title": "전기반 대시보드",
        "workctrs": ["전기반", "합자회사 동화-전기"],
        "label_map": {"합자회사 동화-전기": "동화(전기)"},
        "nav": "dashboard_electric",
    },
    "mechanical": {
        "title": "기계반 대시보드",
        "workctrs": ["기계반", "수산인더스트리-기계"],
        "label_map": {"수산인더스트리-기계": "수산(기계)"},
        "nav": "dashboard_mechanical",
    },
    "instrument": {
        "title": "장치반 대시보드",
        "workctrs": ["장치반", "수산인더스트리-장치", "수산인더스트리-영선"],
        "label_map": {
            "수산인더스트리-장치": "수산(장치)",
            "수산인더스트리-영선": "수산(영선)",
        },
        "nav": "dashboard_instrument",
    },
    "meter": {
        "title": "계기반 대시보드",
        "workctrs": ["계기반", "합자회사 동화-계기"],
        "label_map": {"합자회사 동화-계기": "동화(계기)"},
        "nav": "dashboard_meter",
    },
}


def _build_payload(df):
    return {
        "trend": dd.trend_by_cost_center(df),
        "damage_trend": dd.damage_trend(df),
        "cost_center_pie": dd.cost_center_pie(df),
        "workctr_pie": dd.workctr_pie(df),
        "cost_chart": dd.cost_monthly(df),
        "workctr_time": dd.workctr_time(df),
        "equipment_damage": dd.equipment_damage(df),
        "status_by_cost": dd.status_by_cost_center(df),
    }


@dashboard_bp.route("/")
def dashboard_page():
    df = load_data()
    if df.empty:
        return "Error: total_data.csv not found or is empty.", 500

    df = dd.preprocess(df)
    payload = _build_payload(df)

    return render_template(
        "dashboard/dashboard.html",
        nav_active="dashboard_main",
        view_title="대시보드 메인",
        view_key=None,
        data=payload,
    )


@dashboard_bp.route("/<view>")
def dashboard_view(view: str):
    config = VIEW_CONFIG.get(view)
    if not config:
        abort(404)

    df = load_data()
    if df.empty:
        return "Error: total_data.csv not found or is empty.", 500

    df = dd.preprocess(df)
    filtered = df[df["WorkCtr.Text"].isin(config["workctrs"])].copy()
    if filtered.empty:
        return f"{config['title']} 데이터가 없습니다.", 404

    payload = _build_payload(filtered)

    return render_template(
        "dashboard/dashboard.html",
        nav_active=config["nav"],
        view_title=config["title"],
        view_key=view,
        data=payload,
    )
