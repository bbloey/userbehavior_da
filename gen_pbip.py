# -*- coding: utf-8 -*-
"""Generate a PBIP (Power BI Desktop project) with TMDL semantic model."""
import os, json, uuid

ROOT = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard"
DATA = os.path.join(ROOT, "data").replace("\\", "/")
SM = os.path.join(ROOT, "TmallUserBehavior.SemanticModel")
DEF = os.path.join(SM, "definition")
RP = os.path.join(ROOT, "TmallUserBehavior.Report")
os.makedirs(os.path.join(DEF, "tables"), exist_ok=True)
os.makedirs(RP, exist_ok=True)

def tag():
    return str(uuid.uuid4())

# table: {columns: [(name, dataType, summarizeBy)], m_types: [(name, mtype)]}
TABLES = {
    "dim_date": {
        "cols": [("date","date","none"),("day","string","none"),("month","string","none"),
                 ("weekday","int64","none"),("is_weekend","int64","sum"),
                 ("is_pre_promo","int64","sum"),("is_double12","int64","sum")],
        "mtypes": [("date","type date"),("day","type text"),("month","type text"),
                   ("weekday","Int64.Type"),("is_weekend","Int64.Type"),
                   ("is_pre_promo","Int64.Type"),("is_double12","Int64.Type")],
        "measures": [],
    },
    "agg_daily_behavior": {
        "cols": [("date","date","none"),("behavior_label","string","none"),
                 ("events","int64","sum"),("users","int64","sum")],
        "mtypes": [("date","type date"),("behavior_label","type text"),
                   ("events","Int64.Type"),("users","Int64.Type")],
        "measures": [],
    },
    "agg_daily_funnel": {
        "cols": [("date","date","none"),("browse","int64","sum"),("favorite","int64","sum"),
                 ("cart","int64","sum"),("purchase","int64","sum"),
                 ("cart_rate","double","sum"),("buy_rate","double","sum"),("cart2buy","double","sum")],
        "mtypes": [("date","type date"),("browse","Int64.Type"),("favorite","Int64.Type"),
                   ("cart","Int64.Type"),("purchase","Int64.Type"),
                   ("cart_rate","type number"),("buy_rate","type number"),("cart2buy","type number")],
        "measures": [
            ("浏览用户数(日)", "SUM(agg_daily_funnel[browse])", "#,0"),
            ("加购用户数(日)", "SUM(agg_daily_funnel[cart])", "#,0"),
            ("购买事件数(日)", "SUM(agg_daily_funnel[purchase])", "#,0"),
            ("浏览→加购率", "DIVIDE([加购用户数(日)], [浏览用户数(日)])", "0.0%"),
            ("浏览→购买率", "DIVIDE([购买事件数(日)], [浏览用户数(日)])", "0.0%"),
            ("加购→购买率", "DIVIDE([购买事件数(日)], [加购用户数(日)])", "0.0%"),
        ],
    },
    "agg_hour_behavior": {
        "cols": [("hour","int64","none"),("behavior_label","string","none"),("events","int64","sum")],
        "mtypes": [("hour","Int64.Type"),("behavior_label","type text"),("events","Int64.Type")],
        "measures": [],
    },
    "agg_daily_category": {
        "cols": [("date","date","none"),("item_category","int64","none"),
                 ("behavior_label","string","none"),("events","int64","sum"),("users","int64","sum")],
        "mtypes": [("date","type date"),("item_category","Int64.Type"),
                   ("behavior_label","type text"),("events","Int64.Type"),("users","Int64.Type")],
        "measures": [],
    },
    "fact_purchase": {
        "cols": [("user_id","int64","sum"),("item_id","int64","none"),
                 ("item_category","int64","none"),("date","date","none"),("hour","int64","none")],
        "mtypes": [("user_id","Int64.Type"),("item_id","Int64.Type"),
                   ("item_category","Int64.Type"),("date","type date"),("hour","Int64.Type")],
        "measures": [],
    },
    "dim_user_rfm": {
        "cols": [("user_id","int64","none"),("last_date","date","none"),("frequency","int64","sum"),
                 ("first_date","date","none"),("distinct_items","int64","sum"),
                 ("active_days","int64","sum"),("recency_days","int64","sum"),
                 ("is_new_buyer","int64","sum"),("r_score","int64","sum"),
                 ("f_score","int64","sum"),("m_score","int64","sum"),("segment","string","none")],
        "mtypes": [("user_id","Int64.Type"),("last_date","type date"),("frequency","Int64.Type"),
                   ("first_date","type date"),("distinct_items","Int64.Type"),
                   ("active_days","Int64.Type"),("recency_days","Int64.Type"),
                   ("is_new_buyer","Int64.Type"),("r_score","Int64.Type"),
                   ("f_score","Int64.Type"),("m_score","Int64.Type"),("segment","type text")],
        "measures": [
            ("买家总数", "DISTINCTCOUNT(dim_user_rfm[user_id])", "#,0"),
            ("人均购买次数", "AVERAGE(dim_user_rfm[frequency])", "#,0.0"),
            ("复购率", "DIVIDE(CALCULATE(DISTINCTCOUNT(dim_user_rfm[user_id]), dim_user_rfm[frequency] > 1), DISTINCTCOUNT(dim_user_rfm[user_id]))", "0.0%"),
        ],
    },
    "cohort_weekly": {
        "cols": [("first_week","date","none"),("aw","date","none"),("user_id","int64","sum"),
                 ("offset_week","int64","none"),("cohort_users","int64","sum"),("retention","double","sum")],
        "mtypes": [("first_week","type date"),("aw","type date"),("user_id","Int64.Type"),
                   ("offset_week","Int64.Type"),("cohort_users","Int64.Type"),("retention","type number")],
        "measures": [],
    },
    "ltv_weekly": {
        "cols": [("first_week","date","none"),("offset_week","int64","none"),
                 ("purchases","int64","sum"),("buyers","int64","sum"),
                 ("cohort_users","int64","sum"),("purch_per_user","double","sum")],
        "mtypes": [("first_week","type date"),("offset_week","Int64.Type"),
                   ("purchases","Int64.Type"),("buyers","Int64.Type"),
                   ("cohort_users","Int64.Type"),("purch_per_user","type number")],
        "measures": [],
    },
    "anomaly_daily_purchase": {
        "cols": [("date","date","none"),("browse","int64","sum"),("cart","int64","sum"),
                 ("favorite","int64","sum"),("purchase","int64","sum"),
                 ("purchase_ma7","double","sum"),("purchase_z","double","sum")],
        "mtypes": [("date","type date"),("browse","Int64.Type"),("cart","Int64.Type"),
                   ("favorite","Int64.Type"),("purchase","Int64.Type"),
                   ("purchase_ma7","type number"),("purchase_z","type number")],
        "measures": [],
    },
}

def m_partition(table, mtypes):
    pairs = ", ".join('{{"{n}", {t}}}'.format(n=n, t=t) for n, t in mtypes)
    return f'''	partition {table} = m
		mode: import
		source =
				let
					Source = Csv.Document(File.Contents("{DATA}/{table}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
					#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
					#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{pairs}}})
				in
					#"Changed Type"
'''

for table, spec in TABLES.items():
    lines = [f"table {table}", f"\tlineageTag: {tag()}", ""]
    for name, expr, fmt in spec["measures"]:
        lines += [f"\tmeasure '{name}' = {expr}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {tag()}", ""]
    for cname, dtype, summ in spec["cols"]:
        lines += [
            f"\tcolumn '{cname}'" if cname == "date" else f"\tcolumn {cname}",
            f"\t\tdataType: {dtype}",
            f"\t\tlineageTag: {tag()}",
            f"\t\tsummarizeBy: {summ}",
            f"\t\tsourceColumn: {cname}",
            "",
            "\t\tannotation SummarizationSetBy = Automatic",
            "",
        ]
    lines.append(m_partition(table, spec["mtypes"]))
    with open(os.path.join(DEF, "tables", f"{table}.tmdl"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

# relationships
RELS = [
    ("rel_date_behavior", "agg_daily_behavior", "date", "dim_date", "date", "many", "one"),
    ("rel_date_funnel", "agg_daily_funnel", "date", "dim_date", "date", "many", "one"),
    ("rel_date_category", "agg_daily_category", "date", "dim_date", "date", "many", "one"),
    ("rel_date_purchase", "fact_purchase", "date", "dim_date", "date", "many", "one"),
    ("rel_date_anomaly", "anomaly_daily_purchase", "date", "dim_date", "date", "many", "one"),
    ("rel_rfm_purchase", "dim_user_rfm", "user_id", "fact_purchase", "user_id", "one", "many"),
]
rel_lines = []
for name, ft, fc, tt, tc, fcard, tcard in RELS:
    rel_lines += [
        f"relationship {name}",
        f"\tlineageTag: {tag()}",
        "",
        f"\tfromTable: {ft}",
        f"\tfromColumn: {fc}",
        f"\tfromCardinality: {fcard}",
        f"\ttoTable: {tt}",
        f"\ttoColumn: {tc}",
        f"\ttoCardinality: {tcard}",
        "",
    ]
with open(os.path.join(DEF, "relationships.tmdl"), "w", encoding="utf-8") as f:
    f.write("\n".join(rel_lines).rstrip() + "\n")

with open(os.path.join(DEF, "database.tmdl"), "w", encoding="utf-8") as f:
    f.write("database\n\tcompatibilityLevel: 1567\n")

with open(os.path.join(DEF, "model.tmdl"), "w", encoding="utf-8") as f:
    f.write("model Model\n\tculture: zh-CN\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\nannotation PBI_QueryOrder = ['dim_date','agg_daily_behavior','agg_daily_funnel','agg_hour_behavior','agg_daily_category','fact_purchase','dim_user_rfm','cohort_weekly','ltv_weekly','anomaly_daily_purchase']\n")

with open(os.path.join(SM, "definition.pbism"), "w", encoding="utf-8") as f:
    json.dump({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "1.0",
        "settings": {}
    }, f, indent=2)

# report shell
with open(os.path.join(RP, "definition.pbir"), "w", encoding="utf-8") as f:
    json.dump({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
        "version": "1.0",
        "datasetReference": {"byPath": {"path": "../TmallUserBehavior.SemanticModel"}}
    }, f, indent=2)

report = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportSchema/1.0.0/schema.json",
    "sections": [{
        "name": "p1e2c3d4e5f6a1b2c3d4",
        "displayName": "电商用户行为看板",
        "displayOption": "FitToPage",
        "ordinal": 0,
        "height": 720,
        "width": 1280,
        "config": "{}",
        "visualContainers": [],
        "filters": "[]"
    }]
}
with open(os.path.join(RP, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

# .pbip entry
with open(os.path.join(ROOT, "TmallUserBehavior.pbip"), "w", encoding="utf-8") as f:
    json.dump({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": "TmallUserBehavior.Report"}}],
        "settings": {"enableAutoRecovery": True}
    }, f, indent=2)

print("PBIP generated at", ROOT)
