import os
import time
from flask import Blueprint, abort, render_template, request, jsonify

from app.services.data_loader import load_data
from app.services import dashboard_data as dd
from app import config

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# 작업반별 대시보드 구성
VIEW_CONFIG = {
    "electric": {
        "title": "전기 대시보드",
        "workctrs": ["전기반", "합자회사 동화-전기"],
        "label_map": {"합자회사 동화-전기": "동화(전기)"},
        "nav": "dashboard_electric",
    },
    "mechanical": {
        "title": "기계 대시보드",
        "workctrs": ["기계반", "수산인더스트리-기계"],
        "label_map": {"수산인더스트리-기계": "수산(기계)"},
        "nav": "dashboard_mechanical",
    },
    "instrument": {
        "title": "계기 대시보드",
        "workctrs": ["계기반", "합자회사 동화-계기"],
        "label_map": {"합자회사 동화-계기": "동화(계기)"},
        "nav": "dashboard_instrument",
    },
    "meter": {
        "title": "장치/영선 대시보드",
        "workctrs": ["장치반", "수산인더스트리-장치", "영진-영선"],
        "label_map": {
            "수산인더스트리-장치": "수산(장치)",
            "영진-영선": "영선",
        },
        "nav": "dashboard_meter",
    },
}

DEFAULT_EQUIPMENT = "1005504"
_PREPROCESS_CACHE = {"df": None, "mtime": 0.0}
_PAYLOAD_CACHE = {"data": {}, "mtime": 0.0}


def _get_preprocessed_df():
    """DB 변경이 없으면 전처리된 DF를 캐시로 재사용."""
    try:
        mtime = config.SAP_DB_PATH.stat().st_mtime
    except Exception:
        mtime = 0.0

    if _PREPROCESS_CACHE["df"] is not None and _PREPROCESS_CACHE["mtime"] == mtime:
        return _PREPROCESS_CACHE["df"]

    df = load_data()
    if df.empty:
        return df

    df = dd.preprocess(df)
    _PREPROCESS_CACHE["df"] = df
    _PREPROCESS_CACHE["mtime"] = mtime
    return df


def _get_payload(view=None):
    """DB가 변하지 않으면 payload까지 캐시해 페이지 진입 속도 단축."""
    try:
        mtime = config.SAP_DB_PATH.stat().st_mtime
    except Exception:
        mtime = 0.0

    key = view or "_main"
    cache_mtime = _PAYLOAD_CACHE.get("mtime", 0.0)
    cache_entry = _PAYLOAD_CACHE["data"].get(key)

    if cache_entry and cache_mtime == mtime:
        return cache_entry

    df = _get_preprocessed_df()
    if df.empty:
        return None

    payload = _build_payload(df if view is None else df, view)
    _PAYLOAD_CACHE["data"][key] = payload
    _PAYLOAD_CACHE["mtime"] = mtime
    return payload


def _build_payload(df, view=None):
    equipment_damage_fn = getattr(dd, "equipment_damage_by_month", None)
    if equipment_damage_fn is None:
        # 안전장치: 구버전 모듈에도 동작하도록 기본 함수로 대체
        def equipment_damage_fn(dataframe, equipment):
            return dd.equipment_damage(dataframe) if hasattr(dd, "equipment_damage") else {"labels": [], "datasets": []}

    """공통 차트 페이로드 구성"""
    payload = {
        "trend": dd.trend_by_cost_center(df),
        "damage_trend": dd.damage_trend(df),
        "cost_center_pie": dd.cost_center_pie(df),
        "workctr_pie": dd.workctr_pie(df),
        "cost_chart": dd.cost_monthly(df),
        "workctr_time": dd.workctr_time(df),
        "equipment_damage": equipment_damage_fn(df, DEFAULT_EQUIPMENT),
        "status_by_cost": dd.status_by_cost_center(df),
        "filter_options": dd.get_filter_options(df),
    }

    # 작업반 대시보드용 비교/비용 차트 추가
    if view and view in VIEW_CONFIG:
        config = VIEW_CONFIG[view]
        comparison_data = dd.workctr_order_and_work_comparison(
            df, config["workctrs"], config.get("label_map", {})
        )
        payload["workctr_comparison"] = comparison_data
        payload["cost_by_center"] = dd.cost_by_cost_center(df, "Total Cost")

    return payload


@dashboard_bp.route("/")
def dashboard_page():
    payload = _get_payload()
    if not payload:
        return "Error: 데이터가 없습니다.", 500

    return render_template(
        "dashboard/dashboard.html",
        nav_active="dashboard_main",
        view_title="정비 대시보드",
        view_key="",
        data=payload,
    )


@dashboard_bp.route("/<view>")
def dashboard_view(view: str):
    config = VIEW_CONFIG.get(view)
    if not config:
        abort(404)

    payload = _get_payload(view)
    if not payload:
        return "Error: 데이터가 없습니다.", 500

    return render_template(
        "dashboard/dashboard.html",
        nav_active=config["nav"],
        view_title=config["title"],
        view_key=view,  # electric, mechanical, instrument, meter
        data=payload,
    )


@dashboard_bp.route("/api/filter-chart", methods=["POST"])
def filter_chart():
    """차트별 필터 적용 API"""
    try:
        data = request.get_json()
        chart_id = data.get("chart_id")
        start_ym = data.get("start_ym")
        end_ym = data.get("end_ym")
        view = data.get("view")  # electric, mechanical 등

        df = _get_preprocessed_df()
        if df.empty:
            return jsonify({"error": "데이터가 없습니다."}), 500

        # view 기준 작업반 필터
        if view and view in VIEW_CONFIG:
            config = VIEW_CONFIG[view]
            df = df[df["WorkCtr.Text"].isin(config["workctrs"])]

        # 기간 필터
        if start_ym and end_ym:
            df = df[(df["년월"] >= start_ym) & (df["년월"] <= end_ym)]

        result = {}

        if chart_id == "trendChart":
            result = dd.trend_by_cost_center(df)
        elif chart_id == "damageChart":
            result = dd.damage_trend(df)
        elif chart_id == "costCenterPie":
            result = dd.cost_center_pie(df)
        elif chart_id == "workctrPie":
            result = dd.workctr_pie(df)
        elif chart_id == "costChart":
            cost_type = data.get("cost_type")
            if cost_type:
                result = dd.cost_monthly_filtered(df, cost_type)
            else:
                result = dd.cost_monthly(df)
        elif chart_id == "workctrTime":
            result = dd.workctr_time(df)
        elif chart_id == "equipmentDamage":
            result = dd.equipment_damage_by_month(df, DEFAULT_EQUIPMENT)
        elif chart_id == "statusCost":
            result = dd.status_by_cost_center(df)
        elif chart_id == "workctrComparison":
            if view and view in VIEW_CONFIG:
                config = VIEW_CONFIG[view]
                result = dd.workctr_order_and_work_comparison(
                    df, config["workctrs"], config.get("label_map", {})
                )
            else:
                result = {"order_count": {"labels": [], "datasets": []}, "actual_work": {"labels": [], "datasets": []}}
        elif chart_id == "costByCenter":
            cost_type = data.get("cost_type", "Total Cost")
            result = dd.cost_by_cost_center(df, cost_type)
        else:
            return jsonify({"error": f"Unknown chart_id: {chart_id}"}), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/filter-equipment-damage", methods=["POST"])
def filter_equipment_damage():
    """Equipment 검색/기간 필터 API"""
    try:
        data = request.get_json()
        equipment = data.get("equipment", "")
        start_ym = data.get("start_ym")
        end_ym = data.get("end_ym")
        view = data.get("view")

        df = _get_preprocessed_df()
        if df.empty:
            return jsonify({"error": "데이터가 없습니다."}), 500

        if view and view in VIEW_CONFIG:
            config = VIEW_CONFIG[view]
            df = df[df["WorkCtr.Text"].isin(config["workctrs"])]

        if start_ym and end_ym:
            df = df[(df["년월"] >= start_ym) & (df["년월"] <= end_ym)]

        equipment_damage_fn = getattr(dd, "equipment_damage_by_month", None)
        if equipment_damage_fn is None and hasattr(dd, "equipment_damage"):
            result = dd.equipment_damage(df)
        elif equipment_damage_fn:
            result = equipment_damage_fn(df, equipment)
        else:
            result = {"labels": [], "datasets": []}

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
