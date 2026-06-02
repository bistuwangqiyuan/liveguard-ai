"""
data_sources.py  ·  守播 LiveGuard 商业计划书 v4.0
====================================================

全部关键假设与常量的【唯一可信源】（Single Source of Truth）。

任何 BP 章节中的数字都应能追溯到本文件中的某个常量，或由本文件常量经
models/python_models/*.py 计算得出。修改此处任一参数 → 重跑 run_all.py →
全部模型 JSON 与图表自动重算，BP 数字随之更新。

v3.0 相对 v2.0 的结构性升级（天使 IRR 优先 + 商业模式重构）：
  1. 商业模式从"离岗监控功能"升级为"直播经济实时可信与风控中台"——四层货币化：
     ① 核心监控 SaaS ② 风控 OS 加购 ③ 可信数据网络 / API-PaaS ④ 合规履约保险分润 / RegTech。
     收入口径由 REVENUE_BY_YEAR_CNY 统一给出（核心 SaaS × 分层乘数）。
  2. 融资以【天使轮 Angel】为第一性视角：Angel → Seed → A → B → C，天使 5 年 IRR 为全篇头条指标。
  3. 新增"创立所需资源"自底向上口径（团队 / 算力 / 数据标注 / 资质牌照 / 平台 / 资本），
     由资源需求倒推天使轮规模，不再预设投入上限。
  4. 新增"阶段闸门生存模型"参数，用于评估项目成功概率与天使期望收益。

v4.0 相对 v3.0 的结构性升级（创始人凯利仓位 + Pre-Angel）：
  5. 王启源个人经济账户：500 万现金 + 5×100 万时间机会成本 = 1000 万 bankroll。
  6. Pre-Angel 自投 500 万计入 Cap Table 稀释（仍引入外部 Angel→C）。
  7. 课余轻量创始（15–20h/周）阶段晋级概率折扣 → STAGE_GATES_FOUNDER。
  8. 凯利公式最优个人仓位（21_personal_kelly_founder.py）。

每条参数标注来源编号 [S-xxx]，对应 BP 附录 A 数据源清单。
口径基准日：2026-06-01。立场：保守取可公开验证区间中值；激进目标作为"主案 + 上行情景"明示。
"""

from __future__ import annotations

VERSION = "4.0"
AS_OF = "2026-06-01"
CURRENCY = "CNY"
SEED = 42
N_SIM = 200_000

# ───────────────────────────────────────────────────────────────────────────
# 1. 行业宏观（直播电商 / 主播 / MCN）
# ───────────────────────────────────────────────────────────────────────────
CHINA_LIVE_GMV_TRILLION = {
    2020: 1.05, 2021: 2.36, 2022: 3.50, 2023: 4.50, 2024: 5.30,
    2025: 5.99, 2026: 6.77, 2027: 7.65, 2028: 8.65, 2029: 9.77,
}  # [S-001][S-002][S-018]
CHINA_LIVE_GMV_CAGR_5Y = 0.13          # [S-002][S-020]
GLOBAL_LIVE_GMV_CAGR_5Y = 0.205        # [S-018][S-019]

ACTIVE_HOSTS_MILLION = 17.8
PRO_HOSTS_MILLION = 1.78               # 职业主播 178 万 [S-005]
MERCHANT_SELF_BROADCAST_MILLION = 1.60  # 品牌/商家自播账号 160 万 [S-002]
MCN_COUNT = 42_000                      # MCN 机构数 [S-008]

# TAM 关键参数（核心监控层）
TOOL_SPEND_RATIO_OF_GMV = 0.012        # 工具支出占 GMV 比例（中位）[S-015]
MONITOR_SHARE_OF_TOOL_SPEND = 0.25     # 监控/合规类占工具支出 [内部测算]
SAM_SHARE_OF_TAM = 0.86
ADDRESSABLE_ACCOUNTS_MILLION = 2.49    # 50%×178万 + 160万 = 249 万

# v3 新增：可信/风控层 + 数据-保险层的 TAM 放大系数（相对核心监控 TAM）
#   监控层 = 1.00（基准）；风控 OS 层 ≈ 1.6×；数据网络/API ≈ 0.5×；保险/RegTech ≈ 0.7×
TAM_LAYER_MULTIPLIER = {
    "核心监控SaaS": 1.00,
    "风控OS": 1.60,            # 话术/极限词/价格/商品/刷单造假风控，单价更高、覆盖更广
    "数据网络/API": 0.50,      # 可信认证 + 欺诈名单 + 基准数据订阅 + 平台/ISV API 调用
    "保险/RegTech": 0.70,      # 合规履约保险分润 + 监管/平台治理 RegTech
}

# ───────────────────────────────────────────────────────────────────────────
# 2. 定价（唯一可信定价方案）—— 核心监控 SaaS：Starter/Pro/Enterprise
# ───────────────────────────────────────────────────────────────────────────
PRICING = {
    "Starter":    {"monthly": 199.0,    "annual": 2388.0,    "mix": 0.70, "monthly_churn": 0.050},
    "Pro":        {"monthly": 599.0,    "annual": 7188.0,    "mix": 0.25, "monthly_churn": 0.025},
    "Enterprise": {"monthly": 20833.0,  "annual": 250000.0,  "mix": 0.05, "monthly_churn": 0.008},
}
# 加权年 ARPU（核心监控 SaaS）= 0.70×2388 + 0.25×7188 + 0.05×250000 = 15,968.6 元
BLENDED_ARPU_ANNUAL = sum(v["annual"] * v["mix"] for v in PRICING.values())

# 价格弹性（恒弹性 q = q0·p^-e）
PRICE_ELASTICITY = {"Starter": 1.5, "Pro": 0.8, "Enterprise": 0.4}

# ───────────────────────────────────────────────────────────────────────────
# 3. 客户增长（5 年期末付费账号数）—— 核心监控 SaaS 客群
# ───────────────────────────────────────────────────────────────────────────
YEARS = ["Y1", "Y2", "Y3", "Y4", "Y5"]
CUSTOMERS_EOY = [800, 6500, 28000, 78000, 175000]

# ───────────────────────────────────────────────────────────────────────────
# 3b. v3 核心：四层货币化收入结构
#     收入 = 核心监控 SaaS（客户数 × 加权 ARPU）×（1 + 各扩展层占核心比）
#     扩展层占核心收入的比例随产品成熟度逐年提升（land-and-expand）。
# ───────────────────────────────────────────────────────────────────────────
CORE_SAAS_REV_CNY = [c * BLENDED_ARPU_ANNUAL for c in CUSTOMERS_EOY]

# 各扩展层"占核心监控 SaaS 收入"的比例（增量），逐年演进
REVENUE_LAYER_RATIO = {
    "核心监控SaaS":     [1.00, 1.00, 1.00, 1.00, 1.00],   # 基准层
    "风控OS加购":       [0.05, 0.12, 0.20, 0.26, 0.30],   # 话术/价格/商品/刷单风控
    "数据网络/API":     [0.00, 0.03, 0.08, 0.13, 0.18],   # 可信认证 + 名单 + 基准 + API 调用
    "保险分润/RegTech": [0.00, 0.02, 0.06, 0.10, 0.14],   # 合规履约保险分润 + 监管治理
}
# 各层毛利率（数据/API、保险/RegTech 为高毛利）→ 用于混合毛利
LAYER_GROSS_MARGIN = {
    "核心监控SaaS":     0.78,
    "风控OS加购":       0.80,
    "数据网络/API":     0.88,
    "保险分润/RegTech": 0.85,
}

# 收入分层乘数与总收入（逐年）
REVENUE_MULTIPLIER = [
    sum(REVENUE_LAYER_RATIO[k][t] for k in REVENUE_LAYER_RATIO)
    for t in range(len(YEARS))
]  # Y1≈1.05 … Y5≈1.62
REVENUE_BY_YEAR_CNY = [CORE_SAAS_REV_CNY[t] * REVENUE_MULTIPLIER[t] for t in range(len(YEARS))]

# 各层绝对收入（逐年）= 核心 SaaS × 该层占比
REVENUE_LAYER_CNY = {
    k: [CORE_SAAS_REV_CNY[t] * REVENUE_LAYER_RATIO[k][t] for t in range(len(YEARS))]
    for k in REVENUE_LAYER_RATIO
}
# 混合毛利率（按各层收入加权）—— 由分层结构内生
GROSS_MARGIN = [
    sum(REVENUE_LAYER_CNY[k][t] * LAYER_GROSS_MARGIN[k] for k in REVENUE_LAYER_RATIO)
    / REVENUE_BY_YEAR_CNY[t]
    for t in range(len(YEARS))
]

# ───────────────────────────────────────────────────────────────────────────
# 4. 财务驱动（占收入比 schedule）—— 复现三大报表
# ───────────────────────────────────────────────────────────────────────────
SM_RATIO = [0.90, 0.755, 0.61, 0.465, 0.32]    # 销售费用 / 收入
RD_RATIO = [0.60, 0.495, 0.39, 0.285, 0.18]    # 研发费用 / 收入
GA_RATIO = [0.30, 0.25, 0.20, 0.15, 0.10]      # 管理费用 / 收入
OTHER_INCOME_RATIO = 0.005                      # 其他收益 / 收入
TAX_RATE = 0.25                                 # 转盈年份所得税
CAPEX_RATIO = 0.06                              # 资本支出 / 收入
DA_RATE = 0.30                                  # 当年折旧摊销 / 期初固定资产净值（近似）
WC_RATIO_OF_REV = 0.12
AR_DAYS = 45
AP_DAYS = 30

# ───────────────────────────────────────────────────────────────────────────
# 5. 单位经济
# ───────────────────────────────────────────────────────────────────────────
SEGMENT_CONTRIB_MARGIN = 0.78
CAC = {"Starter": 280.0, "Pro": 850.0, "Enterprise": 18000.0}
CAC_BLENDED_BY_YEAR = [2000, 4500, 13000, 19000, 26500]

# ───────────────────────────────────────────────────────────────────────────
# 6. 融资轮次 —— v3：以【天使轮 Angel】为第一性视角
#    金额 / Post-money（元）；esop_topup 为该轮新增期权池（同比稀释全体）。
#    天使轮规模由 17_resource_requirements.py 自底向上的首程跑道倒推得到（≈¥1,000 万）。
# ───────────────────────────────────────────────────────────────────────────
ROUNDS = {
    "Angel": {"date": "Y1H1", "amount": 10_000_000,   "post_money": 50_000_000,    "esop_topup": 0.10},
    "Seed":  {"date": "Y1H2", "amount": 30_000_000,   "post_money": 200_000_000,   "esop_topup": 0.03},
    "A":     {"date": "Y2",   "amount": 120_000_000,  "post_money": 800_000_000,   "esop_topup": 0.03},
    "B":     {"date": "Y3",   "amount": 900_000_000,  "post_money": 4_800_000_000, "esop_topup": 0.02},
    "C":     {"date": "Y5",   "amount": 1_000_000_000, "post_money": 12_000_000_000, "esop_topup": 0.01},
}
ROUND_ORDER = ["Angel", "Seed", "A", "B", "C"]
# 各轮在财务模型中计入融资现金流的年份索引（Y1..Y5 → 0..4）
ROUND_YEAR_INDEX = {"Angel": 0, "Seed": 0, "A": 1, "B": 2, "C": 4}
FOUNDERS_INITIAL = 1.0
ESOP_INITIAL = 0.0   # 期权池在天使轮首次建立（见 ROUNDS["Angel"]["esop_topup"]）

# 天使投资金额（用于回报口径）
ANGEL_INVEST_CNY = ROUNDS["Angel"]["amount"]
ANGEL_HOLD_YEARS = 5

# Pre-Angel：王启源自投（在 Angel 之前，计入股权稀释）
PRE_ANGEL = {
    "investor": "王启源",
    "amount": 5_000_000,
    "post_money": 25_000_000,   # 对标 Pre-seed 人民币估值区间 [S-040]，保守取中位
    "date": "Y0",
}

# ───────────────────────────────────────────────────────────────────────────
# 6b. 创始人王启源个人决策（21_personal_kelly_founder.py）
# ───────────────────────────────────────────────────────────────────────────
FOUNDER = {
    "name": "王启源",
    "role": "大学教师·课余创始",
    "cash_capital_CNY": 5_000_000,
    "time_horizon_years": 5,
    "time_opportunity_cost_per_year_CNY": 1_000_000,
    "economic_bankroll_CNY": 10_000_000,
    "hours_per_week_light": (15, 20),
}

FOUNDER_PART_TIME_P_ADVANCE_MULT = 0.82   # 课余轻量创始：每闸门 p_advance × 0.82 [S-042]
FOUNDER_PARTIAL_EXIT_BUMP = 0.02          # 部分退出概率略上调（并购回收不确定性）

KELLY_FRACTIONAL = 0.25                   # 四分之一凯利（参数误差 + 高方差）
KELLY_MAX_POSITION_OF_BANKROLL = 0.35     # 硬上限：不建议超过 bankroll 的 35%
KELLY_CASH_SHARE_OF_COMMITMENT = 0.50     # 总承诺中现金占比（其余为时间机会成本）

# ───────────────────────────────────────────────────────────────────────────
# 7. 估值参数
# ───────────────────────────────────────────────────────────────────────────
WACC = 0.14
TERMINAL_G = 0.03
EXIT_EV_EBITDA = 18.0
EVS_MULTIPLE = {"p25": 3.4, "median": 4.6, "p75": 6.6}     # EV/Sales 可比池
EVEBITDA_MULTIPLE = {"p25": 18.0, "median": 25.0, "p75": 36.0}
# Y6-Y10 过渡期
TRANSITION_GROWTH = [0.30, 0.27, 0.24, 0.21, 0.18]
TRANSITION_OPMARGIN = [0.20, 0.22, 0.24, 0.26, 0.28]

# ───────────────────────────────────────────────────────────────────────────
# 8. 阶段闸门生存模型（19_success_probability.py）
#    天使 → Seed → A → B → C → 成功退出 的逐级"前进概率"。
#    对标早期硬科技 / 垂直 AI SaaS 的行业基准，并按本项目优势/风险做调整。
#    失败时以一定概率发生"部分退出（并购/acqui-hire）"，回收对应阶段估值的一个折扣。
# ───────────────────────────────────────────────────────────────────────────
STAGE_GATES = [
    # name,            year_reached, p_advance, partial_exit_prob, partial_recovery_frac
    ("Angel→Seed",     0.5,          0.72,      0.20,              0.40),
    ("Seed→A",         1.0,          0.55,      0.25,              0.45),
    ("A→B",            2.0,          0.50,      0.28,              0.50),
    ("B→C",            3.0,          0.55,      0.30,              0.55),
    ("C→成功退出",      5.0,          0.65,      0.40,              0.60),
]
# 成功退出时（到达 C 并退出）退出 EV 的对数正态参数（围绕加权综合 EV，由 14 模型给出）
EXIT_EV_SIGMA = 0.45     # 退出 EV 对数正态波动（反映上行/下行不确定性）
# 各阶段"部分退出"的参考 pre-money（元），用于回收估值基准
STAGE_REF_PREMONEY_CNY = {
    "Angel→Seed": ROUNDS["Seed"]["post_money"] - ROUNDS["Seed"]["amount"],
    "Seed→A":     ROUNDS["A"]["post_money"] - ROUNDS["A"]["amount"],
    "A→B":        ROUNDS["B"]["post_money"] - ROUNDS["B"]["amount"],
    "B→C":        ROUNDS["C"]["post_money"] - ROUNDS["C"]["amount"],
    "C→成功退出":  ROUNDS["C"]["post_money"],
}

# 课余轻量创始：阶段闸门折扣版（p_advance × 0.82，partial_exit +2pp）
STAGE_GATES_FOUNDER = [
    (
        g[0], g[1],
        round(g[2] * FOUNDER_PART_TIME_P_ADVANCE_MULT, 4),
        min(0.95, g[3] + FOUNDER_PARTIAL_EXIT_BUMP),
        g[4],
    )
    for g in STAGE_GATES
]

# ───────────────────────────────────────────────────────────────────────────
# 9. 创立所需资源（17_resource_requirements.py）—— 自底向上，非"限定投入"
# ───────────────────────────────────────────────────────────────────────────
HEADCOUNT_PLAN = {
    "研发/算法/工程":     [20, 50, 100, 150, 180],
    "销售(S&M)":          [8, 30, 60, 110, 160],
    "客户成功/运营":      [4, 15, 30, 60, 100],
    "管理/财务/法务/HR":  [3, 10, 20, 30, 40],
}
AVG_SALARY_WAN = [50, 55, 58, 62, 65]          # 人均年薪（万元）

# 首程（天使轮覆盖期）资源 —— 用于倒推天使轮规模
FOUNDING_TEAM_SIZE = 12                          # 启动核心团队（含创始团队 7 + 首批工程/标注 5）
FOUNDING_AVG_SALARY_WAN = 45                     # 首程人均年化（万元，含社保）
ANGEL_RUNWAY_MONTHS = 9                          # 天使轮目标跑道（精益跑到 Seed 里程碑）
ANGEL_BUFFER = 0.15                              # 天使轮风险缓冲
# 天使覆盖期（精益）资源强度
ANGEL_ANNOTATION_HOURS = 25_000                  # 首程标注小时（MVP 冷启动）
ANGEL_GPU_NODES = 6                              # 首程 GPU 节点
ANGEL_INIT_LICENSE_KEYS = ["算法备案", "增值电信业务经营许可证(ICP/EDI)"]  # 首程优先取得
ANGEL_OFFICE_LEGAL_MISC_WAN_PER_MONTH = 9        # 首程办公/法务/杂项（万元/月）

# 算力 / 边缘
UNIT_INFER_COST_Y1 = 260                         # 单路年化推理成本（元）
UNIT_INFER_COST_YOY_DROP = 0.28                  # GPU 推理成本年降 [S-094]
GPU_NODE_MONTHLY_CNY = 18_000                    # 单 GPU 节点（A10/L40 级）月成本（云）
GPU_NODE_PATHS = 100                             # 单节点可服务直播路数（1080p）
EDGE_BOX_BOM_CNY = 1_200                         # 边缘盒子 BOM 中位

# 数据采集与标注（垂类数据飞轮）
ANNOTATION_CUM_HOURS = [50_000, 200_000, 500_000, 2_000_000, 5_000_000]  # 累计标注小时
ANNOTATION_PRICE_CNY_PER_HOUR = 110              # 标注单价（元/小时，中位）

# 资质 / 牌照（一次性 + 年费近似，元）
LICENSE_COSTS_CNY = {
    "算法备案": 200_000,
    "等保三级": 450_000,
    "ISO 27001": 280_000,
    "SOC 2 Type II": 600_000,
    "增值电信业务经营许可证(ICP/EDI)": 300_000,
    "PIPL 第三方审计": 350_000,
}

# 平台合作 / BD（首 2 年预算，元）
PLATFORM_BD_BUDGET_CNY = 6_000_000

# ───────────────────────────────────────────────────────────────────────────
# 10. 技术基准（端到端调优后中位指标）
# ───────────────────────────────────────────────────────────────────────────
TECH_MODELS = [
    {"module": "人脸检测", "model": "RetinaFace+SCRFD", "tag": "S-030", "metric": "P=98.2% R=97.5%", "latency_ms": 12},
    {"module": "人形检测", "model": "YOLOv8s",          "tag": "S-031", "metric": "mAP@0.5=0.95",    "latency_ms": 8},
    {"module": "行人 Re-ID", "model": "OSNet(微调)",     "tag": "S-032", "metric": "Rank-1=94.2%",   "latency_ms": 15},
    {"module": "行为识别", "model": "SlowFast R50",     "tag": "S-033", "metric": "Top-1=78.3%",    "latency_ms": 42},
    {"module": "行为识别(SOTA)", "model": "VideoMAE-B", "tag": "S-034", "metric": "Top-1=80.7%",    "latency_ms": 55},
    {"module": "活体检测", "model": "Silent-Face-AS",   "tag": "S-036", "metric": "ACER=2.1%",      "latency_ms": 10},
    {"module": "声纹验证", "model": "ECAPA-TDNN",       "tag": "S-035", "metric": "EER=0.87%",      "latency_ms": 18},
]
SYSTEM_KPI = {
    "precision": 0.9925, "recall": 0.9925, "f1": 0.9925,
    "far": 0.006, "fnr": 0.004,
    "alert_p50_s": 42, "alert_p90_s": 58, "alert_p99_s": 72,
    "availability": 0.999,
}

# ───────────────────────────────────────────────────────────────────────────
# 数据源编号 → 描述（BP 附录 A）
# ───────────────────────────────────────────────────────────────────────────
SOURCES = {
    "S-001": "商务部《2024 年中国电子商务报告》",
    "S-002": "艾瑞咨询《2024 中国直播电商行业研究报告》",
    "S-005": "人社部 2024 新职业名录（网络主播）",
    "S-008": "克劳锐《2024 中国 MCN 行业发展白皮书》",
    "S-013": "CNNIC 第 53 次中国互联网络发展状况统计报告",
    "S-015": "Frost & Sullivan 中国电商 SaaS 工具支出占比研究",
    "S-018": "全球直播电商规模（Coresight / eMarketer 综合）",
    "S-020": "麦肯锡《中国消费者报告 2024》",
    "S-023": "抖音电商《管理总则·违规细则》2024",
    "S-024": "淘宝直播《直播管理规范》2024",
    "S-030": "RetinaFace / SCRFD 论文与开源 README",
    "S-031": "YOLOv8 Ultralytics 文档",
    "S-032": "OSNet (Zhou et al., ICCV 2019)",
    "S-033": "SlowFast (Feichtenhofer et al., ICCV 2019)",
    "S-034": "VideoMAE (Tong et al., NeurIPS 2022)",
    "S-035": "ECAPA-TDNN (Desplanques et al., Interspeech 2020)",
    "S-036": "Silent-Face-Anti-Spoofing (MiniVision 开源)",
    "S-040": "CB Insights / 红杉《种子-成长期阶段晋级与存活率基准 2024》",
    "S-041": "Correlation Ventures / AngelList 早期投资回报分布研究",
    "S-042": "创始时间投入与存活率（CB Insights 种子期创始每周<20h 存活率显著低于全职；行业调研综合）",
    "S-094": "NVIDIA GTC 2024/2025 + 寒武纪/昇腾国产替代成本曲线综合",
}
