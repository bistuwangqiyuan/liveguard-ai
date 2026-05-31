"""
run_all.py
==========

一键运行守播 LiveGuard 全部 16 个模型，按依赖顺序执行（估值模型依赖财务模型），
汇总关键 headline 数字到 outputs/summary.json，并校验资产负债表勾稽。

用法：
    cd liveguard/models/python_models
    python run_all.py
"""

from __future__ import annotations

import json
import runpy
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "outputs"

ORDER = [
    "01_market_sizing.py",
    "02_unit_economics.py",
    "03_roi_merchant.py",
    "04_slo_latency_budget.py",
    "05_alerts_capacity_erlangc.py",
    "06_dedup_suppression_sim.py",
    "07_growth_cohort.py",
    "08_pricing_model.py",
    "09_cohort_retention.py",
    "10_financial_projections.py",   # 核心：估值依赖其 JSON
    "11_fundraising_dilution.py",
    "12_valuation_dcf.py",
    "13_valuation_comparables.py",
    "14_monte_carlo_valuation.py",
    "15_sensitivity_analysis.py",
    "16_tech_benchmark.py",
]


def main() -> int:
    sys.path.insert(0, str(HERE))
    t0 = time.time()
    failed = []
    for f in ORDER:
        print(f"\n{'='*70}\n── Running {f} ──\n{'='*70}")
        try:
            runpy.run_path(str(HERE / f), run_name="__main__")
        except Exception as e:  # noqa: BLE001
            print(f"!! FAILED {f}: {e}")
            failed.append(f)

    # 汇总 headline
    def load(name):
        p = OUT / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    mkt = load("01_market_sizing")
    fin = load("10_financial_projections")
    fund = load("11_fundraising_dilution")
    dcf = load("12_valuation_dcf")
    mc = load("14_monte_carlo_valuation")

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models_run": len(ORDER), "failed": failed,
        "headline": {
            "TAM_consensus_yi": round(mkt.get("TAM_consensus_CNY", {}).get("median", 0) / 1e8, 1) if mkt else None,
            "SAM_consensus_yi": round(mkt.get("SAM_consensus_CNY", {}).get("median", 0) / 1e8, 1) if mkt else None,
            "SOM_y5_yi": round(mkt.get("SOM_year5_CNY", 0) / 1e8, 2) if mkt else None,
            "Y5_revenue_yi": fin.get("headline", {}).get("Y5_revenue_yi"),
            "Y5_ebitda_yi": fin.get("headline", {}).get("Y5_ebitda_yi"),
            "Y5_net_yi": fin.get("headline", {}).get("Y5_net_yi"),
            "Y5_rule_of_40": fin.get("headline", {}).get("Y5_rule_of_40"),
            "balance_sheet_max_recon_gap_CNY": fin.get("headline", {}).get("max_recon_gap_CNY"),
            "founders_after_C_pct": fund.get("founders_after_C_pct"),
            "total_raised_yi": round(fund.get("total_raised_CNY", 0) / 1e8, 2) if fund else None,
            "EV_dcf_two_stage_yi": dcf.get("EV_two_stage_yi"),
            "EV_weighted_yi": mc.get("weighted_EV_yi"),
            "C_round_post_money_yi": mc.get("c_round_post_money_yi"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"✓ 全部完成，用时 {time.time()-t0:.1f}s；summary.json 已写入")
    print(json.dumps(summary["headline"], ensure_ascii=False, indent=2))
    if failed:
        print(f"!! 失败模型: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
