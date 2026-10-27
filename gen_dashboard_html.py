# -*- coding: utf-8 -*-
"""Generate interactive plotly HTML dashboard from prepared star-schema CSVs."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import os

DATA = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard\data"
OUT = r"C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard"
os.chdir(DATA)

LB = {"browse": "浏览", "favorite": "收藏", "cart": "加购", "purchase": "购买"}
CLR = {"浏览": "#5470c6", "收藏": "#91cc75", "加购": "#fac858", "购买": "#ee6666"}

daily = pd.read_csv("agg_daily_behavior.csv", parse_dates=["date"])
daily["行为"] = daily["behavior_label"].map(LB)
funnel = pd.read_csv("agg_daily_funnel.csv", parse_dates=["date"])
hour = pd.read_csv("agg_hour_behavior.csv")
hour["行为"] = hour["behavior_label"].map(LB)
cat = pd.read_csv("agg_daily_category.csv")
rfm = pd.read_csv("dim_user_rfm.csv")
coh = pd.read_csv("cohort_weekly.csv", parse_dates=["first_week", "aw"])
ltv = pd.read_csv("ltv_weekly.csv", parse_dates=["first_week"])
anom = pd.read_csv("anomaly_daily_purchase.csv", parse_dates=["date"])
audit = pd.read_csv("audit_summary.csv", index_col=0)
audit.columns = ["value"]

# KPIs
total_events = int(audit.loc["rows_clean", "value"])
pur_events = int(funnel["purchase"].sum())
buyers = len(rfm)
rep = (rfm["frequency"] > 1).mean()
freq = rfm["frequency"].mean()
browse_u, cart_u, pur_u = funnel["browse"].sum(), funnel["cart"].sum(), funnel["purchase"].sum()
conv = pur_u / browse_u

figs = []

# ---- 1 daily trend ----
f1 = px.line(daily, x="date", y="events", color="行为", color_discrete_map=CLR,
             title="每日行为事件趋势（清洗后）", markers=True)
f1.update_layout(hovermode="x unified", legend_title="")
figs.append(("trend", f1))

# ---- 2 conversion funnel rates ----
f2 = go.Figure()
f2.add_trace(go.Scatter(x=funnel["date"], y=funnel["cart_rate"] * 100, name="浏览→加购率", line={"color": "#fac858"}))
f2.add_trace(go.Scatter(x=funnel["date"], y=funnel["buy_rate"] * 100, name="浏览→购买率", line={"color": "#ee6666"}))
f2.add_trace(go.Scatter(x=funnel["date"], y=funnel["cart2buy"] * 100, name="加购→购买率", line={"color": "#5470c6"}))
f2.update_layout(title="每日转化率（%，按去重用户数）", yaxis_title="%", hovermode="x unified")
figs.append(("conv", f2))

# ---- 3 funnel overview ----
f3 = go.Figure(go.Funnel(
    y=["浏览", "加购", "购买"],
    x=[browse_u, cart_u, pur_u],
    textinfo="value+percent initial", marker={"color": ["#5470c6", "#fac858", "#ee6666"]}))
f3.update_layout(title="整体转化漏斗（31天去重用户数）")
figs.append(("funnel", f3))

# ---- 4 hour distribution ----
f4 = px.bar(hour, x="hour", y="events", color="行为", color_discrete_map=CLR, barmode="group",
            title="24小时行为分布")
f4.update_layout(xaxis_title="小时", yaxis_title="事件数")
figs.append(("hour", f4))

# ---- 5 top categories by purchase ----
top_cat = (cat[cat["behavior_label"] == "purchase"].groupby("item_category")["events"].sum()
           .sort_values(ascending=False).head(20).reset_index())
top_cat["类目ID"] = top_cat["item_category"].astype(str)
f5 = px.bar(top_cat, x="类目ID", y="events", title="Top 20 购买类目（购买事件数）",
            color_discrete_sequence=["#ee6666"])
f5.update_layout(xaxis_title="类目", yaxis_title="购买事件数")
figs.append(("topcat", f5))

# ---- 6 RFM segments ----
seg = rfm["segment"].value_counts().reset_index()
seg.columns = ["segment", "n"]
seg["占比"] = seg["n"] / seg["n"].sum()
SEGC = {"Champions": "#ee6666", "Loyal": "#fac858", "Potential": "#91cc75",
        "New / Promising": "#5470c6", "At Risk": "#fc8452", "Hibernating": "#73c0de"}
f6 = px.pie(seg, names="segment", values="n", hole=0.45,
            color="segment", color_discrete_map=SEGC,
            title=f"RFM 用户分群（{buyers:,} 名买家）")
f6.update_traces(textinfo="label+percent")
figs.append(("rfm", f6))

# ---- 7 cohort retention heatmap ----
piv = coh.pivot_table(index="first_week", columns="offset_week", values="retention", aggfunc="first")
lab = piv.index.strftime("%m-%d周")
f7 = go.Figure(go.Heatmap(z=piv.values * 100, x=[f"第{int(c)}周" for c in piv.columns], y=lab,
                          colorscale="RdYlGn_r", zmid=50, text=np.round(piv.values * 100, 1),
                          texttemplate="%{text}%", colorbar={"title": "留存%"}))
f7.update_layout(title="周cohort留存热力图（首购周 → 后续周回购用户占比）", yaxis_title="首购周", xaxis_title="周偏移")
figs.append(("cohort", f7))

# ---- 8 LTV proxy ----
f8 = px.line(ltv, x="offset_week", y="purch_per_user", color=ltv["first_week"].dt.strftime("%m-%d首购周"),
             markers=True, title="简化LTV：首购cohort人均每周购买量")
f8.update_layout(xaxis_title="周偏移", yaxis_title="人均购买量", legend_title="cohort")
figs.append(("ltv", f8))

# ---- 9 anomaly ----
f9 = go.Figure()
f9.add_trace(go.Bar(x=anom["date"], y=anom["purchase"], name="购买事件数", marker_color="#a6c8ff"))
f9.add_trace(go.Scatter(x=anom["date"], y=anom["purchase_ma7"], name="7日移动均值", line={"color": "#ee6666", "width": 3}))
spike = anom[anom["purchase_z"].abs() > 2]
if len(spike):
    f9.add_trace(go.Scatter(x=spike["date"], y=spike["purchase"], mode="markers+text",
                            name="异常点(|z|>2)", marker={"color": "red", "size": 12, "symbol": "diamond"},
                            text=[f"z={v:.1f}" for v in spike["purchase_z"]], textposition="top center"))
f9.update_layout(title="购买事件异常检测（z-score vs 7日均线）", hovermode="x unified", bargap=0)
figs.append(("anomaly", f9))

# ---- assemble HTML ----
cards = f"""
<div class="cards">
  <div class="card"><div class="v">{total_events:,}</div><div class="l">清洗后行为事件</div></div>
  <div class="card"><div class="v">{pur_events:,}</div><div class="l">购买事件(GMV代理)</div></div>
  <div class="card"><div class="v">{buyers:,}</div><div class="l">活跃购买用户</div></div>
  <div class="card"><div class="v">{rep*100:.1f}%</div><div class="l">复购率(≥2次购买)</div></div>
  <div class="card"><div class="v">{freq:.1f}</div><div class="l">人均购买次数</div></div>
  <div class="card"><div class="v">{conv*100:.2f}%</div><div class="l">浏览→购买转化率</div></div>
</div>"""

plot_divs = []
for i, (fid, fig) in enumerate(figs):
    include_js = "cdn" if i == 0 else False
    plot_divs.append(f'<div class="fig">{fig.to_html(full_html=False, include_plotlyjs=include_js)}</div>')

html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>天猫用户行为与用户价值看板</title>
<style>
body{{font-family:'Microsoft YaHei',sans-serif;margin:0;background:#f4f6fa;color:#333}}
.head{{background:linear-gradient(90deg,#1f3b73,#2b5876);color:#fff;padding:22px 36px}}
.head h1{{margin:0;font-size:24px}} .head p{{margin:6px 0 0;opacity:.85;font-size:13px}}
.cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;padding:18px 36px}}
.card{{background:#fff;border-radius:10px;padding:14px 10px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.card .v{{font-size:22px;font-weight:700;color:#1f3b73}} .card .l{{font-size:12px;color:#888;margin-top:4px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 36px 30px}}
.fig{{background:#fff;border-radius:10px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.full{{grid-column:1/3}}
h2{{margin:0 0 6px;font-size:16px;color:#1f3b73}}
.sec{{padding:0 36px 10px}}
.note{{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:14px}}
.note li{{margin:4px 0;font-size:13.5px}}
</style></head><body>
<div class="head"><h1>天猫用户行为与用户价值看板</h1>
<p>数据：tianchi_fresh_comp_train_user.csv · 2014-11-18 ~ 2014-12-18（31天）· 清洗后 11,785,920 条行为记录 · 交互图可悬停/缩放/点击图例</p></div>
{cards}
<div class="sec"><h2>核心结论</h2><div class="note"><ul>
<li><b>大促驱动显著</b>：12-12 为唯一强异常日，购买事件 27,292（约为日常 7 日均值的 3 倍，z=5.4），窗口内无其他异常点，行为呈"脉冲型"而非稳态。</li>
<li><b>转化瓶颈在加购→购买</b>：浏览→加购约 30%+，加购→购买均值 66.4%、最低日仅 47.8%（大促蓄水期），大量加购未转化，可通过催付/降价提醒收割。</li>
<li><b>复购率高但窗口短</b>：31 天内 91% 买家有 ≥2 次购买，人均 11.7 次——含同品多次下单记录，跨月真实留存需更长窗口。</li>
<li><b>新客获取逐周递减</b>：首购用户集中在观测窗口起点（11-17 当周 9,816 人，含数据截断效应），此后逐周下滑，12-15 当周首购仅 390 人——大促并未带来持续拉新，新客沉淀不足。</li>
<li><b>At Risk + Hibernating 占 40%</b>：RFM 分群中高风险与沉睡用户合计约 4 成，是大促后召回的主要目标。</li>
</ul></div>
<h2>行动建议（附预期收益与验证）</h2><div class="note"><ul>
<li>① <b>加购催付自动化</b>：对加购未购买用户 24h 内推送提醒。预期指标：加购→购买率 +3~5pct；验证：随机分流 A/B，观察 7 日转化差。风险：打扰导致退订率上升。</li>
<li>② <b>Top 类目供给保障</b>：Top20 购买类目备货与活动资源倾斜。预期指标：类目 GMV 代理 +8%；验证：干预类目 vs 对照类目 DID。风险：马太效应挤压长尾。</li>
<li>③ <b>At Risk 用户召回</b>：对 recency≥5 天且曾购买用户发放定向券。预期指标：30 天回购率 +5%；验证：券随机发放 A/B。风险：券羊毛党。</li>
<li>④ <b>新客二次转化</b>：12 月首购新客 7 日内二次触达（首购伴随推荐）。预期指标：新客 14 日复购率 +4pct；验证：有/无触达队列对照。风险：成本随量上升。</li>
<li>⑤ <b>大促脉冲平滑</b>：大促前 3 天预热内容种草分流，避免服务端与物流峰值。预期指标：峰值日履约超时率下降；验证：同比双11/双12履约指标。风险：预热过早透支需求。</li>
</ul></div></div>
<div class="grid">
{''.join(plot_divs)}
<div class="fig full"><h2>数据字典与清洗规则</h2><div class="note"><ul>
<li><b>粒度</b>：原始数据 1 行 = 1 用户 × 1 商品 × 1 行为 × 1 小时；无金额/国家字段（geohash 53% 缺失且加密，弃用）。</li>
<li><b>字段</b>：user_id 用户 / item_id 商品 / behavior_type 行为(1浏览 2收藏 3加购 4购买) / item_category 类目 / time 事件时间(精确到小时)。</li>
<li><b>清洗规则</b>：R1 去完全重复(原因:同小时同行为重复上报,影响面368万行,回滚:保留原始CSV可重跑)；R2 geohash 整列弃用；R3 时间窗口校验(无越界)；R4 购买事件数为GMV代理(无金额)。</li>
<li><b>不确定性</b>：behavior_type=4 是否含已取消订单未知；31 天窗口使复购率/LTV 偏乐观；类目为匿名 ID，无品类语义。</li>
</ul></div></div>
</div></body></html>"""

out = os.path.join(OUT, "天猫用户行为分析看板.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML written:", out, "size:", os.path.getsize(out))
