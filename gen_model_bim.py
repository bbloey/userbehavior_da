# -*- coding: utf-8 -*-
"""Generate legacy model.bim (Tabular JSON) for PBIP - replaces TMDL approach."""
import os, json, uuid

ROOT = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard"
SM = os.path.join(ROOT, "TmallUserBehavior.SemanticModel")
DATA = os.path.join(ROOT, "data").replace("\\", "/")

# remove TMDL artifacts
for sub in ("definition", "definition.pbism"):
    p = os.path.join(SM, sub)
    if os.path.isdir(p):
        import shutil; shutil.rmtree(p)
    elif os.path.exists(p):
        os.remove(p)

def tag():
    return str(uuid.uuid4())

# name: (columns[(name,dataType,summarizeBy)], m_transform_pairs, measures[(name,expr,fmt)])
DT = {"date": "dateTime", "string": "string", "int64": "int64", "double": "double"}
TABLES = {
    "dim_date": (
        [("date","date","none"),("day","string","none"),("month","string","none"),
         ("weekday","int64","none"),("is_weekend","int64","sum"),
         ("is_pre_promo","int64","sum"),("is_double12","int64","sum")],
        [("date","type date"),("day","type text"),("month","type text"),
         ("weekday","Int64.Type"),("is_weekend","Int64.Type"),
         ("is_pre_promo","Int64.Type"),("is_double12","Int64.Type")],
        []),
    "agg_daily_behavior": (
        [("date","date","none"),("behavior_label","string","none"),
         ("events","int64","sum"),("users","int64","sum")],
        [("date","type date"),("behavior_label","type text"),
         ("events","Int64.Type"),("users","Int64.Type")],
        []),
    "agg_daily_funnel": (
        [("date","date","none"),("browse","int64","sum"),("favorite","int64","sum"),
         ("cart","int64","sum"),("purchase","int64","sum"),
         ("cart_rate","double","sum"),("buy_rate","double","sum"),("cart2buy","double","sum")],
        [("date","type date"),("browse","Int64.Type"),("favorite","Int64.Type"),
         ("cart","Int64.Type"),("purchase","Int64.Type"),
         ("cart_rate","type number"),("buy_rate","type number"),("cart2buy","type number")],
        [("浏览用户数(日)", "SUM(agg_daily_funnel[browse])", "#,0"),
         ("加购用户数(日)", "SUM(agg_daily_funnel[cart])", "#,0"),
         ("购买事件数(日)", "SUM(agg_daily_funnel[purchase])", "#,0"),
         ("浏览→加购率", "DIVIDE([加购用户数(日)], [浏览用户数(日)])", "0.0%"),
         ("浏览→购买率", "DIVIDE([购买事件数(日)], [浏览用户数(日)])", "0.0%"),
         ("加购→购买率", "DIVIDE([购买事件数(日)], [加购用户数(日)])", "0.0%")]),
    "agg_hour_behavior": (
        [("hour","int64","none"),("behavior_label","string","none"),("events","int64","sum")],
        [("hour","Int64.Type"),("behavior_label","type text"),("events","Int64.Type")],
        []),
    "agg_daily_category": (
        [("date","date","none"),("item_category","int64","none"),
         ("behavior_label","string","none"),("events","int64","sum"),("users","int64","sum")],
        [("date","type date"),("item_category","Int64.Type"),
         ("behavior_label","type text"),("events","Int64.Type"),("users","Int64.Type")],
        []),
    "fact_purchase": (
        [("user_id","int64","sum"),("item_id","int64","none"),
         ("item_category","int64","none"),("date","date","none"),("hour","int64","none")],
        [("user_id","Int64.Type"),("item_id","Int64.Type"),
         ("item_category","Int64.Type"),("date","type date"),("hour","Int64.Type")],
        []),
    "dim_user_rfm": (
        [("user_id","int64","none"),("last_date","date","none"),("frequency","int64","sum"),
         ("first_date","date","none"),("distinct_items","int64","sum"),
         ("active_days","int64","sum"),("recency_days","int64","sum"),
         ("is_new_buyer","int64","sum"),("r_score","int64","sum"),
         ("f_score","int64","sum"),("m_score","int64","sum"),("segment","string","none")],
        [("user_id","Int64.Type"),("last_date","type date"),("frequency","Int64.Type"),
         ("first_date","type date"),("distinct_items","Int64.Type"),
         ("active_days","Int64.Type"),("recency_days","Int64.Type"),
         ("is_new_buyer","Int64.Type"),("r_score","Int64.Type"),
         ("f_score","Int64.Type"),("m_score","Int64.Type"),("segment","type text")],
        [("买家总数", "DISTINCTCOUNT(dim_user_rfm[user_id])", "#,0"),
         ("人均购买次数", "AVERAGE(dim_user_rfm[frequency])", "#,0.0"),
         ("复购率", "DIVIDE(CALCULATE(DISTINCTCOUNT(dim_user_rfm[user_id]), dim_user_rfm[frequency] > 1), DISTINCTCOUNT(dim_user_rfm[user_id]))", "0.0%")]),
    "cohort_weekly": (
        [("first_week","date","none"),("aw","date","none"),("user_id","int64","sum"),
         ("offset_week","int64","none"),("cohort_users","int64","sum"),("retention","double","sum")],
        [("first_week","type date"),("aw","type date"),("user_id","Int64.Type"),
         ("offset_week","Int64.Type"),("cohort_users","Int64.Type"),("retention","type number")],
        []),
    "ltv_weekly": (
        [("first_week","date","none"),("offset_week","int64","none"),
         ("purchases","int64","sum"),("buyers","int64","sum"),
         ("cohort_users","int64","sum"),("purch_per_user","double","sum")],
        [("first_week","type date"),("offset_week","Int64.Type"),
         ("purchases","Int64.Type"),("buyers","Int64.Type"),
         ("cohort_users","Int64.Type"),("purch_per_user","type number")],
        []),
    "anomaly_daily_purchase": (
        [("date","date","none"),("browse","int64","sum"),("cart","int64","sum"),
         ("favorite","int64","sum"),("purchase","int64","sum"),
         ("purchase_ma7","double","sum"),("purchase_z","double","sum")],
        [("date","type date"),("browse","Int64.Type"),("cart","Int64.Type"),
         ("favorite","Int64.Type"),("purchase","Int64.Type"),
         ("purchase_ma7","type number"),("purchase_z","type number")],
        []),
}

tables = []
order = []
for tname, (cols, mt, measures) in TABLES.items():
    order.append(tname)
    tcols = []
    for cname, dt, summ in cols:
        c = {"name": cname, "dataType": DT[dt], "lineageTag": tag(),
             "summarizeBy": summ, "sourceColumn": cname,
             "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]}
        tcols.append(c)
    pairs = ", ".join('{{"{n}", {t}}}'.format(n=n, t=t) for n, t in mt)
    expr = (
        'let\n'
        f'    Source = Csv.Document(File.Contents("{DATA}/{tname}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
        '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
        f'    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{pairs}}})\n'
        'in\n'
        '    #"Changed Type"'
    )
    part = {"name": tname, "mode": "import",
            "source": {"type": "m", "expression": expr}}
    t = {"name": tname, "lineageTag": tag(), "columns": tcols, "partitions": [part]}
    if measures:
        t["measures"] = [{"name": n, "expression": e, "formatString": f, "lineageTag": tag()}
                         for n, e, f in measures]
    tables.append(t)

RELS = [
    ("rel_date_behavior", "agg_daily_behavior", "date", "dim_date", "date"),
    ("rel_date_funnel", "agg_daily_funnel", "date", "dim_date", "date"),
    ("rel_date_category", "agg_daily_category", "date", "dim_date", "date"),
    ("rel_date_purchase", "fact_purchase", "date", "dim_date", "date"),
    ("rel_date_anomaly", "anomaly_daily_purchase", "date", "dim_date", "date"),
    ("rel_rfm_purchase", "dim_user_rfm", "user_id", "fact_purchase", "user_id"),
]
relationships = []
for name, ft, fc, tt, tc in RELS:
    r = {"name": name,
         "fromTable": ft, "fromColumn": fc, "fromCardinality": "many",
         "toTable": tt, "toColumn": tc, "toCardinality": "one"}
    relationships.append(r)

model = {
    "name": "TmallUserBehavior",
    "id": str(uuid.uuid4()),
    "compatibilityLevel": 1550,
    "model": {
        "culture": "zh-CN",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "queryGroups": [],
        "tables": tables,
        "relationships": relationships,
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(order)}],
    },
}

with open(os.path.join(SM, "model.bim"), "w", encoding="utf-8") as f:
    json.dump(model, f, ensure_ascii=False)
print("model.bim written:", os.path.join(SM, "model.bim"))
