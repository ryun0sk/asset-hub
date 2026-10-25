#!/usr/bin/env python3
"""保存済みの独自モデルと公開アナリスト値の差を再現する。ネットワーク不要。"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYMBOLS = ["AVGO", "000660.KS", "2382.TW", "6669.TW", "SMCI"]


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def gap(own, other):
    return (own / other - 1) * 100


def main():
    inputs = read("analyst-comparison-sources.json")
    sources = {x["id"]: x for x in inputs["entries"]}
    model = {
        (r["symbol"], r["year"]): r
        for r in read("results.json")["rows"]
        if r["symbol"] in SYMBOLS and r["case"] == "base"
    }
    rows = []
    for symbol in SYMBOLS:
        current = model[(symbol, 2028)]
        future = model[(symbol, 2029)]
        row = {
            "symbol": symbol,
            "currency": current["quote_currency"],
            "own_2028": {
                k: current[k]
                for k in ["revenue_bn", "operating_income_bn", "normal_net_income_bn",
                          "diluted_shares_bn", "eps_quote_currency"]
            },
            "own_2029_EPS": future["eps_quote_currency"],
            "own_2029_terminal_PE": future["terminal_pe"],
            "own_2029_conditional_present_price": future["conditional_entry_price"],
            "price": current["price"],
            "EPS_gap_is_not_prediction_error": True,
        }
        if symbol == "000660.KS":
            other = sources["fnguide-sk"]
            row.update({
                "external_source_id": "fnguide-sk",
                "external_2028_EPS": other["2028_EPS"],
                "same_calendar_period": True,
                "fully_reconciled_accounting_basis": False,
                "EPS_arithmetic_gap_pct": gap(current["eps_quote_currency"], other["2028_EPS"]),
                "revenue_gap_pct": gap(current["revenue_bn"], other["2028_revenue_bn"]),
                "operating_income_gap_pct": gap(current["operating_income_bn"], other["2028_operating_income_bn"]),
                "external_2028_OPM": other["2028_operating_income_bn"] / other["2028_revenue_bn"],
                "external_NI_div_EPS_shares_bn_reference": other["2028_parent_net_income_bn"] / other["2028_EPS"],
            })
        elif symbol in ["2382.TW", "6669.TW"]:
            source_id = "factset-quanta" if symbol == "2382.TW" else "factset-wiwynn"
            other = sources[source_id]
            row.update({
                "external_source_id": source_id,
                "same_calendar_period": True,
                "fully_reconciled_accounting_basis": False,
                "external_2028_EPS_median": other["2028_EPS_median"],
                "external_2028_EPS_mean": other["2028_EPS_mean"],
                "EPS_arithmetic_gap_vs_median_pct": gap(current["eps_quote_currency"], other["2028_EPS_median"]),
                "EPS_arithmetic_gap_vs_mean_pct": gap(current["eps_quote_currency"], other["2028_EPS_mean"]),
                "revenue_gap_vs_median_pct": gap(current["revenue_bn"], other["2028_revenue_bn_median"]),
            })
        elif symbol == "AVGO":
            # 簡易調整。Broadcom自身・各社のnon-GAAP定義を再現したものではない。
            row["illustrative_adjusted_2028_EPS"] = current["eps_quote_currency"] + (12 + 5.641833333333334) * .82 / 5.05
            row["illustrative_adjusted_2029_EPS"] = future["eps_quote_currency"] + (13 + 4.484833333333334) * .82 / 5.1
            other = sources["marketscreener-avgo"]
            row.update({
                "external_source_id": "marketscreener-avgo",
                "external_FY2028_EPS_reference": other["FY2028_EPS"],
                "same_calendar_period": False,
                "fully_reconciled_accounting_basis": False,
                "EPS_gap_not_computed_due_to_period_and_basis": True,
                "external_NI_div_EPS_shares_bn_reference": other["FY2028_net_income_bn"] / other["FY2028_EPS"],
            })
        else:
            other = sources["marketscreener-smci"]
            proxy = (other["FY2028_revenue_bn"] + other["FY2029_revenue_bn"]) / 2
            row.update({
                "external_source_id": "sp-smci",
                "external_FY2028_adjusted_EPS_reference": sources["sp-smci"]["FY2028_EPS"],
                "same_calendar_period": False,
                "fully_reconciled_accounting_basis": False,
                "EPS_gap_not_computed_due_to_period_and_basis": True,
                "CY2028_revenue_half_year_weight_proxy_bn": proxy,
                "own_revenue_vs_calendar_proxy_gap_pct": gap(current["revenue_bn"], proxy),
                "proxy_caveat": "0.5*FY2028+0.5*FY2029 ignores seasonality and intra-year ramp; not reported CY consensus",
            })
        row["own_2028_OPM"] = current["operating_income_bn"] / current["revenue_bn"]
        # 分析者の倍率と同一の評価法と主張せず、当方利益だけを固定した感応度。
        alternative_pe = {"AVGO": 20, "000660.KS": 7, "2382.TW": 12, "6669.TW": 12, "SMCI": 8}[symbol]
        alternative_price = future["eps_quote_currency"] * alternative_pe / (1.12 ** future["discount_years"])
        row["own_terminal_PE_sensitivity_only"] = {
            "alternative_PE": alternative_pe,
            "conditional_present_price": alternative_price,
            "price_gap_pct": gap(alternative_price, current["price"]),
        }
        assert abs(current["normal_net_income_bn"] / current["diluted_shares_bn"] - current["eps_quote_currency"]) < 1e-6
        rows.append(row)
    assert len(rows) == 5
    assert all(not r["fully_reconciled_accounting_basis"] for r in rows)
    out = {
        "as_of": inputs["as_of"],
        "price_date": inputs["price_date"],
        "status": "comparison of scenarios and dated public forecasts; not accuracy validation or backtest",
        "input_sha256": {name: sha(name) for name in ["results.json", "analyst-comparison-sources.json"]},
        "rows": rows,
        "checks": {"EPS_identity": "5 of 5 passed", "period_basis_not_silently_equated": True,
                   "no_future_consensus_imputation": True, "no_price_or_original_model_mutation": True},
    }
    (HERE / "analyst-comparison.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("Analyst comparison: five companies; saved inputs only; EPS identities passed.")


if __name__ == "__main__":
    main()
