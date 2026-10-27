# -*- coding: utf-8 -*-
"""Prepare star-schema CSVs for Power BI from tianchi_fresh_comp_train_user.csv."""
import pandas as pd
import numpy as np
import os

SRC = r"C:\Users\14362\Desktop\文件\数据分析库\阿里巴巴集团服务类商品用户行为和品类分析\tianchi_fresh_comp_train_user.csv"
OUT = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard\data"
os.makedirs(OUT, exist_ok=True)

BEHAVIOR = {1: "browse", 2: "favorite", 3: "cart", 4: "purchase"}

print("reading csv ...")
df = pd.read_csv(
    SRC,
    dtype={"user_id": "int64", "item_id": "int64", "behavior_type": "int8",
           "user_geohash": "string", "item_category": "int64", "time": "string"},
)
print("rows:", len(df))
print(df.head())

# ---------- quality audit ----------
audit = {}
audit["rows_raw"] = int(len(df))
audit["null_geohash"] = int(df["user_geohash"].isna().sum())
audit["null_category"] = int(df["item_category"].isna().sum())
audit["invalid_behavior"] = int((~df["behavior_type"].isin(BEHAVIOR.keys())).sum())
audit["dup_rows"] = int(df.duplicated(subset=["user_id", "item_id", "behavior_type", "time"]).sum())

# time parse
dt = pd.to_datetime(df["time"].str.slice(0, 10), format="%Y-%m-%d", errors="coerce")
audit["bad_date"] = int(dt.isna().sum())
audit["date_min"] = str(dt.min())
audit["date_max"] = str(dt.max())
hour = pd.to_numeric(df["time"].str.slice(11), errors="coerce")
audit["bad_hour"] = int(hour.isna().sum() | ((hour < 0) | (hour > 23)).sum())
audit["date_out_of_range"] = int(((dt < "2014-11-18") | (dt > "2014-12-18")).sum())

df["date"] = dt.dt.date
df["hour"] = hour.astype("Int16")
df["behavior_label"] = df["behavior_type"].map(BEHAVIOR)

# drop exact duplicates (user,item,behavior,time) -> keep first
df = df.drop_duplicates(subset=["user_id", "item_id", "behavior_type", "time"])
audit["rows_clean"] = int(len(df))

pd.Series(audit).to_csv(os.path.join(OUT, "audit_summary.csv"), encoding="utf-8-sig")
print(audit)

# ---------- dim_date ----------
dates = pd.date_range("2014-11-18", "2014-12-18", freq="D")
dim_date = pd.DataFrame({"date": dates.date})
dim_date["day"] = dim_date["date"].astype(str).str.slice(8, 10)
dim_date["month"] = dim_date["date"].astype(str).str.slice(0, 7)
dim_date["weekday"] = pd.to_datetime(dim_date["date"]).dt.dayofweek + 1  # 1=Mon
dim_date["is_weekend"] = dim_date["weekday"].isin([6, 7]).astype(int)
dim_date["is_pre_promo"] = (dim_date["date"] >= pd.Timestamp("2014-12-01").date()).astype(int)
dim_date["is_double12"] = (dim_date["date"] == pd.Timestamp("2014-12-12").date()).astype(int)
dim_date.to_csv(os.path.join(OUT, "dim_date.csv"), index=False, encoding="utf-8-sig")

# ---------- agg daily behavior ----------
agg_daily = (df.groupby(["date", "behavior_label"], as_index=False)
               .agg(events=("user_id", "size"), users=("user_id", "nunique")))
agg_daily.to_csv(os.path.join(OUT, "agg_daily_behavior.csv"), index=False, encoding="utf-8-sig")

# ---------- agg daily x category x behavior ----------
agg_cat = (df.groupby(["date", "item_category", "behavior_label"], as_index=False)
             .agg(events=("user_id", "size"), users=("user_id", "nunique")))
agg_cat.to_csv(os.path.join(OUT, "agg_daily_category.csv"), index=False, encoding="utf-8-sig")
print("agg_daily_category rows:", len(agg_cat))

# ---------- agg hour behavior ----------
agg_hour = (df.groupby(["hour", "behavior_label"], as_index=False)
              .agg(events=("user_id", "size")))
agg_hour.to_csv(os.path.join(OUT, "agg_hour_behavior.csv"), index=False, encoding="utf-8-sig")

# ---------- funnel per day (browse->cart->purchase users) ----------
piv = (df.groupby(["date", "behavior_label"])["user_id"].nunique().unstack(fill_value=0)
         .reset_index().rename(columns=str.lower))
for c in ["browse", "favorite", "cart", "purchase"]:
    if c not in piv.columns:
        piv[c] = 0
piv["cart_rate"] = piv["cart"] / piv["browse"]
piv["buy_rate"] = piv["purchase"] / piv["browse"]
piv["cart2buy"] = piv["purchase"] / piv["cart"]
piv.to_csv(os.path.join(OUT, "agg_daily_funnel.csv"), index=False, encoding="utf-8-sig")

# ---------- fact_purchase (row grain, cleaned) ----------
pur = df.loc[df["behavior_type"] == 4, ["user_id", "item_id", "item_category", "date", "hour"]].copy()
pur.to_csv(os.path.join(OUT, "fact_purchase.csv"), index=False, encoding="utf-8-sig")
print("fact_purchase rows:", len(pur))

# ---------- RFM ----------
END = pd.Timestamp("2014-12-18")
rfm = (pur.groupby("user_id")
          .agg(last_date=("date", "max"), frequency=("date", "size"),
               first_date=("date", "min"), distinct_items=("item_id", "nunique"),
               active_days=("date", "nunique")))
rfm["recency_days"] = (END - pd.to_datetime(rfm["last_date"])).dt.days
# new-customer flag: first purchase after 2014-12-01 (promo window)
rfm["is_new_buyer"] = (pd.to_datetime(rfm["first_date"]) >= pd.Timestamp("2014-12-01")).astype(int)

def score(col, asc=True):
    q = rfm[col].rank(method="first", pct=True)
    return pd.cut(q, bins=[0, .2, .4, .6, .8, 1.0], labels=[1, 2, 3, 4, 5]).astype(int)

rfm["r_score"] = score("recency_days")            # smaller recency -> better
rfm["f_score"] = score("frequency")               # larger freq -> better
rfm["m_score"] = score("distinct_items")          # M proxy: distinct purchased items

def seg(row):
    if row["r_score"] >= 4 and row["f_score"] >= 4:
        return "Champions"
    if row["r_score"] >= 4 and row["f_score"] <= 2:
        return "New / Promising"
    if row["r_score"] >= 3 and row["f_score"] >= 3:
        return "Loyal"
    if row["r_score"] <= 2 and row["f_score"] >= 3:
        return "At Risk"
    if row["r_score"] <= 2 and row["f_score"] <= 2:
        return "Hibernating"
    return "Potential"

rfm["segment"] = rfm.apply(seg, axis=1)
rfm = rfm.reset_index()
rfm.to_csv(os.path.join(OUT, "dim_user_rfm.csv"), index=False, encoding="utf-8-sig")
print("rfm users:", len(rfm))
print(rfm["segment"].value_counts())

# ---------- repurchase rate ----------
freq = rfm["frequency"]
print("single-purchase users:", int((freq == 1).sum()), "/", len(rfm),
      "=> repeat-buyer rate:", round((freq > 1).mean(), 4))

# ---------- weekly cohort (first purchase week -> later activity) ----------
pur["dt"] = pd.to_datetime(pur["date"])
pur["cohort_week"] = pur["dt"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date())
firstw = pur.groupby("user_id")["cohort_week"].min().rename("first_week")
pur2 = pur.merge(firstw, on="user_id")
act = pur2.groupby(["first_week", "date"])["user_id"].nunique().reset_index()
act["offset_days"] = (pd.to_datetime(act["date"]) - pd.to_datetime(act["first_week"])).dt.days
act["offset_week"] = (act["offset_days"] // 7).astype(int)
coh_size = pur2.groupby("first_week")["user_id"].nunique().rename("cohort_users")
act = act.merge(coh_size, on="first_week")
# users active in a given offset week
actw = (pur2.assign(aw=pur2["dt"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date()))
            .groupby(["first_week", "aw"])["user_id"].nunique().reset_index())
actw["offset_week"] = ((pd.to_datetime(actw["aw"]) - pd.to_datetime(actw["first_week"])).dt.days // 7).astype(int)
actw = actw.merge(coh_size, on="first_week")
actw["retention"] = actw["user_id"] / actw["cohort_users"]
actw.to_csv(os.path.join(OUT, "cohort_weekly.csv"), index=False, encoding="utf-8-sig")

# ---------- LTV proxy: purchases per user per offset week ----------
pur2["offset_week"] = ((pur2["dt"] - pur2["first_week"].pipe(pd.to_datetime)).dt.days // 7).astype(int)
ltv = pur2.groupby(["first_week", "offset_week"], as_index=False).agg(
    purchases=("item_id", "size"), buyers=("user_id", "nunique"))
ltv = ltv.merge(coh_size, on="first_week")
ltv["purch_per_user"] = ltv["purchases"] / ltv["cohort_users"]
ltv.to_csv(os.path.join(OUT, "ltv_weekly.csv"), index=False, encoding="utf-8-sig")

# ---------- anomaly helper: daily purchase stats vs 7d rolling ----------
d = agg_daily.pivot(index="date", columns="behavior_label", values="events").fillna(0).reset_index()
d.columns = [str(c).lower() for c in d.columns]
if "purchase" in d.columns:
    d["purchase_ma7"] = d["purchase"].rolling(7, center=True, min_periods=3).mean()
    d["purchase_z"] = (d["purchase"] - d["purchase"].mean()) / d["purchase"].std()
    d.to_csv(os.path.join(OUT, "anomaly_daily_purchase.csv"), index=False, encoding="utf-8-sig")

print("DONE -> ", OUT)
