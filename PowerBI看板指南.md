# Power BI 看板使用指南 —— 天猫用户行为数据（2014-11-18 ~ 2014-12-18）

## 一、已完成的接入

- 数据源：`tianchi_fresh_comp_train_user.csv`（15,463,110 行）
- 工程位置：`C:\Users\14362\WorkBuddy\2026-10-22-19-10-44\pbi_dashboard\`
  - `TmallUserBehavior.pbip` —— 双击即可用 Power BI Desktop 打开（已打开）
  - `TmallUserBehavior.SemanticModel\model.bim` —— 星型语义模型
  - `data\*.csv` —— 清洗后的星型模型数据表
- Power BI 内已建好 **6 组表关系**（5 张日粒度表挂日期维度 + RFM↔购买事实按 user_id 关联）

## 二、数据字典（已落地的表）

| 表 | 粒度 | 字段 | 用途 |
|---|---|---|---|
| dim_date | 1行/天 | date, day, month, weekday, is_weekend, is_pre_promo, is_double12 | 日期维度 |
| agg_daily_behavior | 天×行为 | date, behavior_label, events, users | 日趋势 |
| agg_daily_funnel | 1行/天 | browse/favorite/cart/purchase 用户数 + 转化率 | 漏斗与转化 |
| agg_hour_behavior | 小时×行为 | hour, behavior_label, events | 时段分布 |
| agg_daily_category | 天×类目×行为 | date, item_category, behavior_label, events, users | Top 类目 |
| fact_purchase | 1行/购买 | user_id, item_id, item_category, date, hour | 购买明细（20.6万行） |
| dim_user_rfm | 1行/买家 | frequency, recency_days, r/f/m_score, segment 等 | 用户分群（17,654人） |
| cohort_weekly | 首购周×自然周 | first_week, offset_week, user_id, retention | 留存 |
| ltv_weekly | 首购周×周偏移 | purchases, buyers, purch_per_user | LTV 代理 |
| anomaly_daily_purchase | 1行/天 | purchase, purchase_ma7, purchase_z | 异常检测 |

behavior_label 取值：browse=浏览(1)、favorite=收藏(2)、cart=加购(3)、purchase=购买(4)

## 三、内置 DAX 度量值（拖到卡片/图表即可用）

转化类（在 agg_daily_funnel 表下）：
- 浏览用户数(日) / 加购用户数(日) / 购买事件数(日)
- 浏览→加购率、浏览→购买率、加购→购买率（格式 0.0%）

用户类（在 dim_user_rfm 表下）：
- 买家总数 = 17,654
- 人均购买次数 ≈ 11.7 次/人
- 复购率 ≈ 91.4%（窗口内购买≥2次的人数占比）

## 四、建议看板版式（第1页「概览」）

1. **顶部 4 张卡片**：购买事件数(日)·SUM(purchase)、买家总数、复购率、浏览→购买率
2. **中部折线图**：X=dim_date.date，Y=agg_daily_behavior.events，图例=behavior_label（可看双12峰值）
3. **漏斗/条形**：浏览→加购→购买（用 agg_daily_funnel 三列用户数）
4. **时段热力**：agg_hour_behavior.events，X=hour，图例=behavior_label
5. **第2页「类目」**：agg_daily_category 按 events 排序的 TopN 条形图（加 TopN 筛选前20）
6. **第3页「用户」**：dim_user_rfm.segment 做环形图；cohort_weekly.retention 做矩阵（行=first_week，列=offset_week）

## 五、关键清洗决策（已在数据层执行）

- 剔除完全重复事件 3,677,190 行（同用户同商品同小时同行为视为重复点击）→ 剩 11,785,920 行
- user_geohash 缺失 8,207,386 行（53%）且已加密不可解析 → 整列弃用
- 时间范围 2014-11-18~12-18 无越界、无非法日期/小时
- 数据无金额字段，"GMV"以购买事件数为代理；无国家字段，改用商品类目做地域替代分析

## 六、注意事项

- 数据仅覆盖 31 天，双12（12-12）前后对比 ≠ 长期趋势
- 复购率高是因"购买"行为含同商品多次下单记录，跨月复购需更长窗口验证
- 原始 CSV 改动后，在 Power BI 中"刷新"即可同步（M 查询按当前路径读取）
