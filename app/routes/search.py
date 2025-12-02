from __future__ import annotations

import io
from typing import Dict, List

import pandas as pd
from flask import Blueprint, abort, render_template, request, send_file, url_for

from app.services import data_store as ds

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
def index():
    store = ds._get_data_store()
    data_available = not store.combined.empty
    limit_value = ds._resolve_limit(request.args.get("limit"))
    selections = {
        "equipment_no": request.args.get("equipment_no", "").strip(),
        "order_no": request.args.get("order_no", "").strip(),
        "equipment_name": request.args.get("equipment_name", "").strip(),
        "top_category": request.args.get("top_category", "").strip(),
        "middle_category": request.args.get("middle_category", "").strip(),
        "sub_category": request.args.get("sub_category", "").strip(),
        "with_links": request.args.get("with_links", "").strip(),
        "detail_query": request.args.get("detail_query", "").strip(),
    }

    search_triggered = request.args.get("search") == "1" or any(
        selections[key] for key in ds.SEARCH_SELECTION_KEYS if key in selections
    )

    selected_orders: List[str] = []
    table_rows: List[Dict[str, object]] = []
    equipment_info = None

    if search_triggered and data_available:
        filtered = ds._apply_filters(store.combined, selections)
        selected_orders = ds._select_order_numbers(filtered, limit_value)
        table_rows = ds._build_table_rows(filtered, selected_orders)
        total_results = filtered["Order No"].nunique()

        if selections.get("equipment_no"):
            equipment_matches = filtered[
                filtered["Equipment"].str.contains(selections["equipment_no"], case=False, na=False)
            ]
            if not equipment_matches.empty:
                first_match = equipment_matches.iloc[0]
                equipment_info = {
                    "number": first_match.get("Equipment", ""),
                    "name": first_match.get("Equi. Text", ""),
                }
    else:
        table_rows = []
        total_results = 0

    result_count = len(selected_orders)

    top_options = [""] + store.top_options

    if selections["top_category"]:
        middle_choices = store.middle_options.get(selections["top_category"], [])
    else:
        middle_choices = store.all_middle_options
    middle_options = [""] + middle_choices

    if selections["top_category"] and selections["middle_category"]:
        sub_choices = store.sub_options.get(
            (selections["top_category"], selections["middle_category"]),
            [],
        )
    elif selections["middle_category"]:
        sub_choices = store.sub_by_middle.get(selections["middle_category"], [])
    elif selections["top_category"]:
        sub_choices = store.sub_by_top.get(selections["top_category"], [])
    else:
        sub_choices = store.all_sub_options
    sub_options = [""] + sub_choices

    equipment_link_template = url_for(
        "search.index",
        middle_category=selections.get("middle_category", ""),
        order_no="",
        equipment_name="",
        top_category="",
        sub_category="",
        equipment_no="EQUIPMENT_PLACEHOLDER",
        with_links=selections.get("with_links", ""),
        search="1",
        limit=limit_value,
    )

    base_params = {
        "equipment_no": selections.get("equipment_no", ""),
        "order_no": selections.get("order_no", ""),
        "equipment_name": selections.get("equipment_name", ""),
        "top_category": selections.get("top_category", ""),
        "middle_category": selections.get("middle_category", ""),
        "sub_category": selections.get("sub_category", ""),
        "with_links": selections.get("with_links", ""),
        "search": "1",
        "limit": limit_value,
    }

    is_limited = total_results > limit_value
    load_more_url = None
    if is_limited:
        load_params = dict(base_params)
        load_params["limit"] = limit_value + ds.DEFAULT_RESULT_LIMIT
        load_more_url = url_for("search.index", **load_params)

    # Build export URL if we have search results
    export_results_url = None
    if search_triggered and data_available and result_count > 0:
        export_params = {
            "equipment_no": selections.get("equipment_no", ""),
            "order_no": selections.get("order_no", ""),
            "equipment_name": selections.get("equipment_name", ""),
            "top_category": selections.get("top_category", ""),
            "middle_category": selections.get("middle_category", ""),
            "sub_category": selections.get("sub_category", ""),
            "with_links": selections.get("with_links", ""),
            "detail_query": selections.get("detail_query", ""),
        }
        export_results_url = url_for("search.export_search_results", **export_params)

    return render_template(
        "search/index.html",
        nav_active="search",
        data_available=data_available,
        show_results=search_triggered and data_available,
        selections=selections,
        top_options=top_options,
        middle_options=middle_options,
        sub_options=sub_options,
        table_rows=table_rows,
        table_columns=ds.TABLE_COLUMNS,
        result_count=result_count,
        total_results=total_results,
        is_limited=is_limited,
        result_limit=limit_value,
        current_dataset_label="전체 데이터 (최신 + 구 SAP)",
        equipment_link_template=equipment_link_template,
        load_more_url=load_more_url,
        equipment_info=equipment_info,
        export_results_url=export_results_url,
    )


@search_bp.route("/order/<order_no>")
def order_detail(order_no: str):
    store = ds._get_data_store()
    combined = store.combined
    target = (order_no or "").strip()

    if not target or combined.empty:
        abort(404)

    mask = combined["Order No"].astype(str).str.strip() == target
    if not mask.any():
        abort(404)

    filtered = combined[mask]
    rows = ds._build_table_rows(filtered, [target])

    if not rows:
        abort(404)

    row_data = rows[0]
    detail_payload = row_data.get("detail_payload", {})

    # Convert empty values to None to hide sections in template
    long_text = detail_payload.get("long_text", "").strip() or None
    materials = detail_payload.get("materials", []) or None
    work_details = detail_payload.get("work_details", []) or None
    dataset_label = row_data.get("dataset_label", "")

    first_row = filtered.iloc[0]

    detail_fields = []
    for label, column in ds.ORDER_INFO_FIELDS:
        value = first_row.get(column, "")
        value = "" if pd.isna(value) else str(value).strip()

        # Format Cost fields with comma and 원
        if "Cost" in column and value and value not in ["-", ""]:
            try:
                # Remove existing commas and convert to number
                num_value = float(value.replace(",", ""))
                # Format with comma separator and add 원
                value = f"{num_value:,.0f} 원"
            except (ValueError, AttributeError):
                pass

        # Format Actual Work with H (hours)
        if column == "Actual Work" and value and value not in ["-", ""]:
            try:
                # Remove existing commas and convert to number
                num_value = float(value.replace(",", ""))
                # Format with comma separator and add H
                value = f"{num_value:,.1f} H"
            except (ValueError, AttributeError):
                pass

        detail_fields.append({"label": label, "value": value})

    if long_text:
        detail_fields.append({"label": "상세내역", "value": long_text})

    return render_template(
        "search/order_detail.html",
        nav_active="search",
        order_no=target,
        detail_fields=detail_fields,
        dataset_label=dataset_label,
        long_text=long_text,
        materials=materials,
        work_details=work_details,
    )


@search_bp.route("/order/<order_no>/export")
def export_order_excel(order_no: str):
    """Export raw order data from database (54 original columns only)"""
    import sqlite3
    from app import config

    target = (order_no or "").strip()
    if not target:
        abort(404)

    # Read directly from database to get original 54 columns
    db_path = config.SHARED_TOTAL_CSV

    try:
        conn = sqlite3.connect(str(db_path))
        # Query only rows matching the order number
        query = "SELECT * FROM sap_reports WHERE \"Order No\" = ?"
        df = pd.read_sql_query(query, conn, params=(target,))
        conn.close()

        if df.empty:
            abort(404)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Order Details")

        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"order_{target}.xlsx",
        )
    except Exception as e:
        print(f"Error exporting order {target}: {e}")
        abort(500)


@search_bp.route("/order/<order_no>/export_detail")
def export_order_detail(order_no: str):
    """Export modal detail view with specific fields only"""
    store = ds._get_data_store()
    combined = store.combined
    target = (order_no or "").strip()

    if not target or combined.empty:
        abort(404)

    mask = combined["Order No"].astype(str).str.strip() == target
    if not mask.any():
        abort(404)

    filtered = combined[mask]
    rows = ds._build_table_rows(filtered, [target])

    if not rows:
        abort(404)

    row_data = rows[0]
    detail_payload = row_data.get("detail_payload", {})

    materials = detail_payload.get("materials", [])
    work_details = detail_payload.get("work_details", [])

    first_row = filtered.iloc[0]

    # Build Excel with specific fields
    excel_data = {
        "Order No": [target],
        "Order Short Text": [first_row.get("Order Short Text", "")],
        "Equipment": [first_row.get("Equipment", "")],
        "설비명": [first_row.get("Equi. Text", "")],
    }

    # Create base DataFrame
    base_df = pd.DataFrame(excel_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Write base info
        base_df.to_excel(writer, index=False, sheet_name="상세내역", startrow=0)

        # Write work details if exists
        if work_details:
            work_df = pd.DataFrame(work_details)
            work_df = work_df.rename(columns={
                "start_of_execution": "Start of Execution",
                "worker_name": "작업자 이름",
                "actual_work": "Actual Work",
                "work_unit": "Unit"
            })
            # Add empty row, then header and data
            start_row = len(base_df) + 3
            worksheet = writer.sheets["상세내역"]
            worksheet.cell(row=start_row, column=1, value="작업 정보")
            work_df.to_excel(writer, index=False, sheet_name="상세내역", startrow=start_row + 1)

        # Write materials if exists
        if materials:
            materials_df = pd.DataFrame(materials)
            materials_df = materials_df.rename(columns={
                "material": "Material",
                "description": "Description",
                "qty": "Qty",
                "uom": "UoM"
            })
            # Calculate start row
            start_row = len(base_df) + 3
            if work_details:
                start_row += len(work_details) + 3
            worksheet = writer.sheets["상세내역"]
            worksheet.cell(row=start_row, column=1, value="자재 정보")
            materials_df.to_excel(writer, index=False, sheet_name="상세내역", startrow=start_row + 1)

    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"order_{target}_detail.xlsx",
    )


@search_bp.route("/export", methods=["GET"])
def export_search_results():
    import sqlite3
    from app import config

    store = ds._get_data_store()
    data_available = not store.combined.empty

    if not data_available:
        abort(404)

    selections = {
        "equipment_no": request.args.get("equipment_no", "").strip(),
        "order_no": request.args.get("order_no", "").strip(),
        "equipment_name": request.args.get("equipment_name", "").strip(),
        "top_category": request.args.get("top_category", "").strip(),
        "middle_category": request.args.get("middle_category", "").strip(),
        "sub_category": request.args.get("sub_category", "").strip(),
        "with_links": request.args.get("with_links", "").strip(),
        "detail_query": request.args.get("detail_query", "").strip(),
    }

    filtered = ds._apply_filters(store.combined, selections)

    if filtered.empty:
        abort(404)

    # Check if full_data parameter is set
    full_data = request.args.get("full_data", "").strip() == "1"

    if full_data:
        # Export all 54 columns from database directly
        try:
            # Get all order numbers (no limit for export)
            all_orders = ds._select_order_numbers(filtered, limit=None)

            if not all_orders:
                abort(404)

            # Read from database directly
            db_path = config.SHARED_TOTAL_CSV
            conn = sqlite3.connect(str(db_path))

            # Create a query for all matching order numbers
            placeholders = ",".join("?" * len(all_orders))
            query = f"SELECT * FROM sap_reports WHERE \"Order No\" IN ({placeholders})"
            export_df = pd.read_sql_query(query, conn, params=all_orders)
            conn.close()

            if export_df.empty:
                abort(404)

            # Sort by date (newest first) using same logic as display
            date_columns = ["Start of Execution", "Bsc start", "Actual Start (Time)", "Required Start"]
            for date_col in date_columns:
                if date_col in export_df.columns:
                    export_df[f"{date_col}_datetime"] = pd.to_datetime(
                        export_df[date_col], errors="coerce"
                    )

            # Create a combined date column for sorting (first non-null date)
            export_df["_sort_date"] = None
            for date_col in date_columns:
                dt_col = f"{date_col}_datetime"
                if dt_col in export_df.columns:
                    export_df["_sort_date"] = export_df["_sort_date"].fillna(export_df[dt_col])

            # Sort by date descending (newest first), then by Equipment and Order No
            export_df = export_df.sort_values(
                by=["_sort_date", "Equipment", "Order No"],
                ascending=[False, True, True],
                na_position="last"
            )

            # Drop temporary sorting columns
            cols_to_drop = ["_sort_date"] + [f"{dc}_datetime" for dc in date_columns if f"{dc}_datetime" in export_df.columns]
            export_df = export_df.drop(columns=cols_to_drop)

            # Insert blank rows between different Order Nos
            export_with_blanks = ds.insert_blank_rows_between_orders(export_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                export_with_blanks.to_excel(writer, index=False, sheet_name="Search Results")

                # Format the worksheet for better readability
                worksheet = writer.sheets["Search Results"]
                ds.format_excel_worksheet(worksheet, export_with_blanks)

            output.seek(0)

            # Determine filename
            equipment_no = selections.get("equipment_no", "").strip()
            if equipment_no:
                download_name = f"{equipment_no}_full_data.xlsx"
            else:
                download_name = "search_results_full_data.xlsx"

            return send_file(
                output,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=download_name,
            )
        except Exception as e:
            print(f"Error exporting full data: {e}")
            abort(500)
    else:
        # Normal export (formatted with work details, materials, etc.)
        # Get all order numbers (no limit for export)
        all_orders = ds._select_order_numbers(filtered, limit=None)
        table_rows = ds._build_table_rows(filtered, all_orders)

        # Build flattened Excel data
        export_df = ds.build_excel_export_data(table_rows)

        if export_df.empty:
            abort(404)

        # Insert blank rows between different Order Nos
        export_with_blanks = ds.insert_blank_rows_between_orders(export_df)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            export_with_blanks.to_excel(writer, index=False, sheet_name="Search Results")

            # Format the worksheet for better readability
            worksheet = writer.sheets["Search Results"]
            ds.format_excel_worksheet(worksheet, export_with_blanks)

        output.seek(0)

        # Determine filename based on Equipment No if available
        equipment_no = selections.get("equipment_no", "").strip()
        if equipment_no:
            download_name = f"{equipment_no}_search_results.xlsx"
        else:
            download_name = "search_results.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=download_name,
        )
