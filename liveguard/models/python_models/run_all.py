"""
run_all.py  ·  守播 LiveGuard v5.0
==================================

一键运行全部 19 个模型，按依赖顺序执行，汇总 headline 到 outputs/summary.json。

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
    "10_financial_projections.py",
    "11_fundraising_dilution.py",
    "12_valuation_dcf.py",
    "13_valuation_comparables.py",
    "14_monte_carlo_valuation.py",
    "15_sensitivity_analysis.py",
    "16_tech_benchmark.py",
    "17_resource_requirements.py",
    "18_angel_returns.py",
    "19_success_probability.py",
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

    def load(name):
        p = OUT / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    mkt = load("01_market_sizing")
    fin = load("10_financial_projections")
    fund = load("11_fundraising_dilution")
    dcf = load("12_valuation_dcf")
    mc = load("14_monte_carlo_valuation")
    res = load("17_resource_requirements")
    lead = load("18_angel_returns")
    succ = load("19_success_probability")

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "5.0", "models_run": len(ORDER), "failed": failed,
        "headline": {
            # —— 市场（单层监控）——
            "TAM_monitor_consensus_yi": round(mkt.get("TAM_consensus_CNY", {}).get("median", 0) / 1e8, 1) if mkt else None,
            "SAM_monitor_consensus_yi": round(mkt.get("SAM_consensus_CNY", {}).get("median", 0) / 1e8, 1) if mkt else None,
            "SOM_Y5_yi": round(mkt.get("SOM_year5_CNY", 0) / 1e8, 2) if mkt else None,
            # —— 财务 ——
            "Y5_revenue_yi": fin.get("headline", {}).get("Y5_revenue_yi"),
            "Y5_ebitda_yi": fin.get("headline", {}).get("Y5_ebitda_yi"),
            "Y5_net_yi": fin.get("headline", {}).get("Y5_net_yi"),
            "Y5_rule_of_40": fin.get("headline", {}).get("Y5_rule_of_40"),
            "balance_sheet_max_recon_gap_CNY": fin.get("headline", {}).get("max_recon_gap_CNY"),
            # —— 融资 / 资源 ——
            "derived_seed_round_yi": round(res.get("angel_stage", {}).get("derived_seed_need_CNY", 0) / 1e8, 2) if res else None,
            "total_raised_yi": round(fund.get("total_raised_CNY", 0) / 1e8, 2) if fund else None,
            "founders_after_C_pct": fund.get("founders_after_C_pct"),
            # —— 估值（2026 压缩倍数）——
            "EV_dcf_two_stage_yi": dcf.get("EV_two_stage_yi"),
            "EV_weighted_yi": mc.get("weighted_EV_yi"),
            "C_round_post_money_yi": mc.get("c_round_post_money_yi"),
            # —— 成功概率与回报（多口径，保守）——
            "lead_round": succ.get("lead_round"),
            "lead_invest_yi": round(lead.get("lead_invest_CNY", 0) / 1e8, 2) if lead else None,
            "lead_final_stake_pct": lead.get("lead_final_stake_pct"),
            "p_success_exit_pct": succ.get("p_success_exit_pct"),
            "p_total_loss_pct": succ.get("p_total_loss_pct"),
            "median_MOIC": succ.get("median_MOIC"),
            "expected_MOIC": succ.get("expected_MOIC"),
            "expected_IRR_path_pct": succ.get("expected_IRR_path_pct"),
            "conditional_success_MOIC": succ.get("conditional_success_MOIC"),
            "conditional_success_IRR_pct": succ.get("conditional_success_IRR_pct"),
            "irr_path_P90_pct": succ.get("irr_path_quantiles_pct", {}).get("P90"),
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
