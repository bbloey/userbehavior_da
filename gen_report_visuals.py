# -*- coding: utf-8 -*-
"""Inject ready-made visuals into the PBIP report.json so the dashboard opens pre-built."""
import json, uuid, os

RP = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard\TmallUserBehavior.Report"
with open(os.path.join(RP, "report.json"), encoding="utf-8") as f:
    report = json.load(f)

def col_ref(src, table, prop):
    return {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}, "Name": f"{table}.{prop}"}

def agg_ref(src, table, prop, func=0, label=None):
    name = label or f"Sum({table}.{prop})"
    return {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}}, "Function": func}, "Name": name}

def meas_ref(src, table, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}, "Name": f"{table}.{prop}"}

def visual(vtype, x, y, w, h, projections, frm, sel):
    cfg = {
        "name": str(uuid.uuid4()),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": vtype,
            "projections": projections,
            "prototypeQuery": {"Version": 2, "From": frm, "Select": sel},
        },
    }
    return {"config": json.dumps(cfg, ensure_ascii=False), "filters": "[]",
            "height": h, "width": w, "x": x, "y": y, "z": 0}

vc = []

# --- KPI cards (row 1) ---
cards = [
    ("复购率", "dim_user_rfm", "r", 0, 0),
    ("买家总数", "dim_user_rfm", "r", 210, 0),
    ("人均购买次数", "dim_user_rfm", "r", 420, 0),
    ("浏览→购买率", "agg_daily_funnel", "f", 630, 0),
    ("购买事件数(日)", "agg_daily_funnel", "f", 840, 0),
]
for prop, table, src, x, y in cards:
    vc.append(visual("card", x, y, 200, 95,
                     {"Values": [{"queryRef": f"{table}.{prop}", "active": True}]},
                     [{"Name": src, "Entity": table, "Type": 0}],
                     [meas_ref(src, table, prop)]))

# --- daily trend line chart ---
vc.append(visual("lineChart", 0, 105, 640, 330,
    {"Category": [{"queryRef": "dim_date.date", "active": True}],
     "Values": [{"queryRef": "Sum(agg_daily_behavior.events)"}],
     "Series": [{"queryRef": "agg_daily_behavior.behavior_label", "active": True}]},
    [{"Name": "d", "Entity": "dim_date", "Type": 0},
     {"Name": "a", "Entity": "agg_daily_behavior", "Type": 0}],
    [col_ref("d", "dim_date", "date"),
     agg_ref("a", "agg_daily_behavior", "events"),
     col_ref("a", "agg_daily_behavior", "behavior_label")]))

# --- hourly column chart ---
vc.append(visual("columnChart", 650, 105, 630, 330,
    {"Category": [{"queryRef": "agg_hour_behavior.hour", "active": True}],
     "Values": [{"queryRef": "Sum(agg_hour_behavior.events)"}],
     "Series": [{"queryRef": "agg_hour_behavior.behavior_label", "active": True}]},
    [{"Name": "h", "Entity": "agg_hour_behavior", "Type": 0}],
    [col_ref("h", "agg_hour_behavior", "hour"),
     agg_ref("h", "agg_hour_behavior", "events"),
     col_ref("h", "agg_hour_behavior", "behavior_label")]))

# --- RFM donut ---
vc.append(visual("donutChart", 0, 445, 420, 275,
    {"Category": [{"queryRef": "dim_user_rfm.segment", "active": True}],
     "Values": [{"queryRef": "Count(dim_user_rfm.user_id)"}]},
    [{"Name": "r", "Entity": "dim_user_rfm", "Type": 0}],
    [col_ref("r", "dim_user_rfm", "segment"),
     agg_ref("r", "dim_user_rfm", "user_id", 4, "Count(dim_user_rfm.user_id)")]))

# --- funnel bar (browse/cart/purchase users) ---
vc.append(visual("barChart", 430, 445, 430, 275,
    {"Values": [
        {"queryRef": "Sum(agg_daily_funnel.browse)", "active": True},
        {"queryRef": "Sum(agg_daily_funnel.cart)", "active": True},
        {"queryRef": "Sum(agg_daily_funnel.purchase)", "active": True}]},
    [{"Name": "f", "Entity": "agg_daily_funnel", "Type": 0}],
    [agg_ref("f", "agg_daily_funnel", "browse"),
     agg_ref("f", "agg_daily_funnel", "cart"),
     agg_ref("f", "agg_daily_funnel", "purchase")]))

# --- weekly active users (cohort table) ---
vc.append(visual("areaChart", 870, 445, 410, 275,
    {"Category": [{"queryRef": "cohort_weekly.aw", "active": True}],
     "Values": [{"queryRef": "Sum(cohort_weekly.user_id)"}]},
    [{"Name": "c", "Entity": "cohort_weekly", "Type": 0}],
    [col_ref("c", "cohort_weekly", "aw"),
     agg_ref("c", "cohort_weekly", "user_id")]))

report["sections"][0]["visualContainers"] = vc
with open(os.path.join(RP, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("visuals injected:", len(vc))
