"""JT dated valuation sensitivities; JPY/share and JPY 100 million (oku).

All assumptions are scenarios, not company guidance or probabilities.
Run from any directory. Only writes JSON to stdout; no network or file mutation.
"""

import json

INPUTS = {
    "as_of_jst": "2026-11-09",
    "reported_company_net_profit_oku": 6620,
    "dividend_basis_company_net_profit_oku": 6600,
    "company_adjusted_operating_profit_oku": 10790,
    "russia_share_of_company_adjusted_operating_profit": 0.25,
    "shares_excluding_treasury_oku": 17.75429749,
    "company_dps_yen": 272,
    "tse_close_yen": 5269,
    "pts_yen": 4735,
    "pts_observed_jst": "2026-11-09 22:04",
    "assumed_russia_marginal_tax_rate": 0.25,
    "assumed_dividend_payout": 0.75,
    "assumed_base_pe": 15,
    "source_financials": "https://www.jti.co.jp/investors/library/presentation/pdf/20261029_03.pdf",
    "source_russia": "https://www.jti.co.jp/investors/library/press_releases/pdf/2026/20261109_01.pdf",
    "source_shares": "https://www.jti.co.jp/investors/library/result/pdf/20261029_01.pdf",
}


def normal_profit(retained=0, tax=0.25, ex_russia_growth=0, extra_after_tax_cost_oku=0):
    """Recurring profit proxy; retained is earnings attributable to JT, not sales."""
    russia_aop = INPUTS["company_adjusted_operating_profit_oku"] * INPUTS["russia_share_of_company_adjusted_operating_profit"]
    russia_net_proxy = russia_aop * (1 - tax)
    ex_russia_profit = INPUTS["dividend_basis_company_net_profit_oku"] - russia_net_proxy
    profit = ex_russia_profit * (1 + ex_russia_growth) + russia_net_proxy * retained - extra_after_tax_cost_oku
    eps = profit / INPUTS["shares_excluding_treasury_oku"]
    return {"profit_oku": profit, "eps_yen": eps,
            "dps_at_75pct_yen": eps * 0.75,
            "dps_at_70pct_yen": eps * 0.70,
            "dps_at_80pct_yen": eps * 0.80,
            "payout_if_272_maintained": 272 / eps}


def annual_cashflows(eps, growth, years, exit_pe, payout=0.75):
    dividends = [eps * (1 + growth) ** t * payout for t in range(1, years + 1)]
    terminal = eps * (1 + growth) ** years * exit_pe
    flows = dividends.copy()
    flows[-1] += terminal
    return dividends, terminal, flows


def irr(price, flows):
    lo, hi = -0.90, 2.0
    for _ in range(120):
        rate = (lo + hi) / 2
        npv = -price + sum(cf / (1 + rate) ** t for t, cf in enumerate(flows, 1))
        if npv > 0:
            lo = rate
        else:
            hi = rate
    return (lo + hi) / 2


def build():
    base = normal_profit()
    scenarios = []
    definitions = [
        ("stress", "ロシアゼロ・非ロシア利益10％減・毎年の追加税後費用150億円", 0, -0.10, 150, 12, 14),
        ("no_russia", "ロシア利益ゼロ", 0, 0, 0, 14, 16),
        ("half_recovery", "JT株主に帰属する従来ロシア経済利益を50％回復", 0.5, 0, 0, 15, 17),
        ("full_recovery", "JT株主に帰属する従来ロシア経済利益を100％回復", 1, 0, 0, 17, 19),
    ]
    for key, label, retained, growth, cost, low, high in definitions:
        case = normal_profit(retained, ex_russia_growth=growth, extra_after_tax_cost_oku=cost)
        scenarios.append({"id": key, "label": label, "retained": retained,
                          "ex_russia_growth": growth, "extra_after_tax_cost_oku": cost,
                          "pe_low": low, "pe_high": high,
                          **case, "fair_low_yen": case["eps_yen"] * low,
                          "fair_high_yen": case["eps_yen"] * high})
    sensitivity = []
    for tax in (0.20, 0.25, 0.30):
        for retained in (0, 0.25, 0.50, 0.75, 1):
            case = normal_profit(retained, tax)
            for pe in (12, 14, 15, 16, 18, 20):
                sensitivity.append({"tax": tax, "retained": retained, "pe": pe,
                                    "eps_yen": case["eps_yen"], "fair_yen": case["eps_yen"] * pe})
    return_cases = []
    for years in (3, 5):
        for growth in (0, 0.04, 0.06):
            dividends, terminal, flows = annual_cashflows(base["eps_yen"], growth, years, 15)
            for price in (3200, 3500, 3600, 3800, 3900, 4000, 4300, 4500, 4735, 5269):
                rate = irr(price, flows)
                residual = -price + sum(cf / (1 + rate) ** t for t, cf in enumerate(flows, 1))
                assert abs(residual) < 1e-7
                return_cases.append({"years": years, "growth": growth, "exit_pe": 15,
                                     "entry_yen": price, "dividends_yen": dividends,
                                     "terminal_yen": terminal, "irr_before_tax": rate,
                                     "max_entry_for_10pct_yen": sum(cf / 1.1 ** t for t, cf in enumerate(flows, 1))})
    ddm = []
    for growth in (0.02, 0.03, 0.04, 0.05):
        for required in (0.09, 0.10, 0.11):
            ddm.append({"growth": growth, "required_return": required,
                        "fair_yen": base["eps_yen"] * .75 * (1 + growth) / (required - growth)})
    stock_metrics = [{"price_yen": p, "pre_event_company_pe": p / 372.88,
                      "no_russia_pe": p / base["eps_yen"],
                      "company_272_yield": 272 / p,
                      "no_russia_75pct_dps_yield": base["dps_at_75pct_yen"] / p}
                     for p in (3500, 3800, 3900, 4000, 4300, 4735, 5269)]
    return {"inputs": INPUTS, "base": base, "base_fair_yen": base["eps_yen"] * 15,
            "tax_cases": [{"tax": t, **normal_profit(tax=t)} for t in (.20, .25, .30)],
            "scenarios": scenarios, "sensitivity": sensitivity,
            "returns": return_cases, "ddm_sensitivity": ddm, "stock_metrics": stock_metrics,
            "limitations": [
                "Russia adjusted operating profit is a proxy; local D&A, financing, tax and stranded overhead are not separately disclosed.",
                "Russian cash repatriation and parent-only cash available for dividends cannot be inferred from consolidated profit or JT FCF.",
                "Recurring-earnings values exclude speculative disposal compensation and extraordinary parent cash costs.",
                "5-year IRRs assume end-of-year annual dividends and sale, before tax and fees; not company guidance.",
                "No scenario probability, price floor or guaranteed return is assigned."]}


if __name__ == "__main__":
    result = build()
    assert abs(6620 / INPUTS["shares_excluding_treasury_oku"] - 372.88) < 0.02
    assert abs(normal_profit(1)["eps_yen"] - 371.75) < 0.02
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
