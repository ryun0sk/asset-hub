"""Recompute conditional earnings/valuation scenarios from saved public inputs.

No network, market feed, proprietary package, or trade execution.
Company-specific modelling adapters are below. All money and share counts use
billions of the specified currency, unless explicitly converted.
"""
import csv
import copy
from datetime import date
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
CASES = ("weak", "base", "strong")
NAMES = {"285A.T": "キオクシア", "NVDA": "NVIDIA", "AVGO": "Broadcom", "TSM": "TSMC ADR",
         "ASML": "ASML米国株", "6857.T": "アドバンテスト", "VRT": "Vertiv", "ANET": "Arista"}


def close(a, b, label, rel=1e-7):
    if abs(a - b) > rel * max(1, abs(a), abs(b)):
        raise ValueError((label, a, b))


def valuation(row, price, terminal_pes, settings):
    years = (date.fromisoformat(settings["target_dates"][str(row["year"])]) -
             date.fromisoformat(settings["price_date"])).days / 365.25
    eps = row["eps_quote_currency"]
    pe = terminal_pes[row["case"]]
    out = dict(row, price=price, terminal_pe=pe, discount_years=years,
               forward_scenario_pe=price / eps if eps > 0 else None,
               terminal_price=eps * pe if eps > 0 else None)
    discount = (1 + settings["required_annual_return"]) ** years
    out["conditional_entry_price"] = eps * pe / discount if eps > 0 else None
    out["entry_price_gap_pct"] = ((out["conditional_entry_price"] / price - 1) * 100
                                  if eps > 0 else None)
    out["required_terminal_pe_for_12pct"] = price * discount / eps if eps > 0 else None
    out["annualized_price_return"] = ((eps * pe / price) ** (1 / years) - 1
                                      if eps > 0 else None)
    out["same_pe25_entry_price"] = eps * 25 / discount if eps > 0 else None
    out["pe_only_sensitivity"] = {str(f): eps * pe * f / discount if eps > 0 else None
                                  for f in (0.75, 1.0, 1.25)}
    out["return_only_sensitivity"] = {
        str(r): eps * pe / (1 + r) ** years if eps > 0 else None
        for r in settings["sensitivity_required_returns"]}
    return out


def network_rows(data):
    for symbol, company in data["companies"].items():
        for r in company["scenarios"]:
            market = r["macro_AI_infrastructure_spend"] * r["allocation_to_AI_addressable_market"]
            ai_revenue = market * r["company_value_share"]
            revenue = ai_revenue + r["non_AI_revenue"]
            op = revenue * r["normal_operating_margin"]
            pretax = op + r["recurring_net_interest_income"]
            ni = pretax * (1 - r["normal_tax_rate"])
            eps = ni / r["diluted_shares"]
            for label, value, saved in (("market", market, r["AI_market"]),
                                        ("revenue", revenue, r["revenue"]),
                                        ("op", op, r["normal_operating_income"]),
                                        ("ni", ni, r["normal_net_income"]),
                                        ("eps", eps, r["normal_EPS"])):
                close(value, saved, (symbol, r["year"], r["case"], label))
            yield {"symbol": symbol, "year": r["year"], "case": r["case"],
                   "financial_currency": "USD", "quote_currency": "USD",
                   "revenue_bn": revenue, "operating_income_bn": op,
                   "normal_net_income_bn": ni, "diluted_shares_bn": r["diluted_shares"],
                   "eps_financial_currency": eps, "eps_quote_currency": eps,
                   "ai_market_bn": market, "company_value_share": r["company_value_share"],
                   "ai_revenue_bn": ai_revenue, "other_revenue_bn": r["non_AI_revenue"],
                   "operating_margin": r["normal_operating_margin"],
                   "net_finance_income_bn": r["recurring_net_interest_income"],
                   "tax_rate": r["normal_tax_rate"],
                   "source_input": "inputs/network-power.json"}


def japan_rows(data, macro):
    fx = data["fx_constants"]["usdjpy"]
    case_map = {"bear": "weak", "base": "base", "bull": "strong"}
    for r in data["rows"]:
        company = data["companies"][r["ticker"]]
        p = company["assumptions"][r["scenario"]]
        y = str(r["year"])
        n = r["year"] - 2026
        case = case_map[r["scenario"]]
        if r["ticker"] == "285A":
            anchor = company["anchor"]
            bit = (1 + p["market_bit_cagr"]) ** n
            market = anchor["annualized_q2_tam_usd_bn"] * bit * p["asp_index"][y]
            brand = market * p["revenue_share"][y] * fx
            local_bit = bit * p["revenue_share"][y] / anchor["q2_2026_kioxia_value_share"] / p["mix_price_premium_index"][y]
            other = anchor["annualized_other_revenue_jpy_bn"] * local_bit ** 0.6
            production = (anchor["economic_production_cost_jpy_bn_residual"] * local_bit *
                          (1 - p["cost_per_bit_annual_decline"]) ** n * p["utilization_cost_penalty"][y])
            fixed = anchor["economic_fixed_cost_jpy_bn_assumed"] * (1 + p["fixed_cost_cagr"]) ** n
            revenue = brand + other
            op = revenue - production - fixed - other
            finance = p["net_finance_jpy_bn"][y]
            symbol = "285A.T"
            close(market, r["nand_tam_usd_bn"], (symbol, y, case, "NAND TAM"))
        elif r["ticker"] == "6857":
            ai = (macro["annual_spend"][y][case] / macro["calibration_2026"]) ** p["capex_elasticity"]
            non = (1 + p["non_ai_cagr"]) ** n
            cycle = p["cycle_multiplier"][y]
            soc = 11 * (p["soc_ai_weight"] * ai * (1 + p["soc_complexity_cagr"]) ** n +
                        (1 - p["soc_ai_weight"]) * non) * cycle
            memory = 2.75 * (p["memory_ai_weight"] * ai * (1 + p["memory_complexity_cagr"]) ** n +
                             (1 - p["memory_ai_weight"]) * non) * cycle
            revenue = (soc * p["soc_share"][y] + memory * p["memory_share"][y]) * fx + p["other_revenue_jpy_bn"][y]
            op = revenue * p["ifrs_op_margin"][y]
            finance = r["normal_net_interest"] / 1e9
            symbol = "6857.T"
            close(soc, r["soc_tam_usd_bn"], (symbol, y, case, "SoC TAM"))
            close(memory, r["memory_tam_usd_bn"], (symbol, y, case, "memory TAM"))
        else:
            anchor = company["anchor"]
            ai = (macro["annual_spend"][y][case] / macro["calibration_2026"]) ** p["ai_capex_elasticity"]
            non = (1 + p["non_ai_cagr"]) ** n
            cycle = p["cycle_multiplier"][y]
            euv_demand = anchor["euv_tam_eur_bn_2026_calibration"] * (
                p["euv_ai_weight"] * ai * (1 + p["euv_exposure_intensity_cagr"]) ** n +
                (1 - p["euv_ai_weight"]) * non) * cycle
            capacity = anchor["euv_tam_eur_bn_2026_calibration"] * 1.3 ** min(n, 2) * 1.15 ** max(n - 2, 0) * 1.03 ** n
            euv = min(euv_demand, capacity)
            duv_tam = anchor["duv_tam_eur_bn_2026_calibration"] * (
                p["duv_ai_weight"] * ai * (1 + p["duv_intensity_cagr"]) ** n +
                (1 - p["duv_ai_weight"]) * non) * cycle
            service = anchor["service_revenue_eur_bn_2026_calibration"] * (1 + p["service_cagr"]) ** n
            metro = anchor["metrology_company_revenue_eur_bn_2026_calibration"] * (1 + p["metrology_cagr"]) ** n
            revenue = euv + duv_tam * p["duv_share"][y] + service + metro
            op = revenue * p["gross_margin"][y] - p["us_gaap_opex_eur_bn"][y]
            finance = r["normal_net_interest"] / 1e9
            symbol = "ASML"
            close(euv, r["euv_delivered_tam_eur_bn"], (symbol, y, case, "delivered EUV"))
        pretax = op + finance
        tax = max(pretax, 0) * p["tax_rate"]
        ni = pretax - tax
        shares_bn = r["diluted_shares"] / 1e9
        eps = ni / shares_bn
        eps_quote = eps * data["fx_constants"]["eurusd"] if symbol == "ASML" else eps
        for label, value, saved in (("revenue", revenue, r["revenue"] / 1e9),
                                    ("op", op, r["normal_operating_profit"] / 1e9),
                                    ("ni", ni, r["normal_parent_profit"] / 1e9),
                                    ("eps", eps, r["eps"])):
            close(value, saved, (symbol, y, case, label))
        yield {"symbol": symbol, "year": r["year"], "case": case,
               "financial_currency": r["currency"], "quote_currency": "USD" if symbol == "ASML" else "JPY",
               "revenue_bn": revenue, "operating_income_bn": op, "normal_net_income_bn": ni,
               "diluted_shares_bn": shares_bn, "eps_financial_currency": eps,
               "eps_quote_currency": eps_quote, "operating_margin": op / revenue,
               "net_finance_income_bn": finance, "tax_rate": p["tax_rate"],
               "source_input": "inputs/japan.json"}


def compute_rows(data, macro):
    for key, company in data["companies"].items():
        symbol = "TSM" if key == "TSMC" else key
        for r in company["forecasts"]:
            pool = macro["annual_spend"][str(r["year"])][r["case"]] * r["eligible_pool_fraction"]
            close(pool, r["eligible_pool_usd_bn"], (symbol, r["year"], r["case"], "pool"))
            if symbol == "TSM":
                upstream = pool * r["upstream_foundry_packaging_content_fraction"] * r["TSMC_upstream_effective_capture"]
                close(upstream, r["upstream_AI_revenue_before_supply_ceiling_usd_bn"], (symbol, "upstream"))
                scale = min(1, r["own_supply_ceiling_usd_bn"] / r["total_revenue_before_supply_ceiling_usd_bn"])
                close(scale, r["supply_scale_factor"], (symbol, "supply ceiling"))
                close(upstream * scale, r["segments"][0]["revenue_usd_bn"], (symbol, "upstream delivery"))
            else:
                for segment in r["segments"]:
                    if "pool_capture" in segment:
                        close(pool * segment["pool_capture"], segment["revenue_usd_bn"], (symbol, segment["name"]))
            revenue = sum(s["revenue_usd_bn"] for s in r["segments"])
            op = (sum(s["revenue_usd_bn"] * s["operating_margin"] for s in r["segments"]) -
                  r["sbc_separate_deduction_usd_bn"] - r["acquired_amortization_separate_deduction_usd_bn"] -
                  r["other_normal_operating_cost_usd_bn"])
            pretax = op + r["normal_net_interest_usd_bn"] + r["normal_other_nonoperating_usd_bn"]
            ni = pretax - max(pretax, 0) * r["tax_rate"] - r["noncontrolling_interest_usd_bn"]
            ordinary_eps = ni / r["diluted_ordinary_shares_bn"]
            quote_eps = ordinary_eps * company["ordinary_shares_per_us_traded_unit"]
            for label, value, saved in (("revenue", revenue, r["calculated"]["revenue_usd_bn"]),
                                        ("op", op, r["calculated"]["operating_profit_usd_bn"]),
                                        ("ni", ni, r["calculated"]["normal_parent_net_income_usd_bn"]),
                                        ("eps", quote_eps, r["calculated"]["eps_usd_per_us_traded_unit"])):
                close(value, saved, (symbol, r["year"], r["case"], label))
            yield {"symbol": symbol, "year": r["year"], "case": r["case"],
                   "financial_currency": "USD", "quote_currency": "USD",
                   "revenue_bn": revenue, "operating_income_bn": op,
                   "normal_net_income_bn": ni, "diluted_shares_bn": r["diluted_ordinary_shares_bn"],
                   "ordinary_shares_per_quoted_unit": company["ordinary_shares_per_us_traded_unit"],
                   "eps_financial_currency": ordinary_eps, "eps_quote_currency": quote_eps,
                   "operating_margin": op / revenue, "net_finance_income_bn": r["normal_net_interest_usd_bn"],
                   "tax_rate": r["tax_rate"], "source_input": "inputs/compute.json"}


def build_rows():
    network = json.loads((BASE / "inputs/network-power.json").read_text())
    macro = json.loads((BASE / "macro.json").read_text())
    rows = list(network_rows(network))
    japan_path = BASE / "inputs/japan.json"
    if japan_path.exists():
        rows += list(japan_rows(json.loads(japan_path.read_text()), macro))
    compute_path = BASE / "inputs/compute.json"
    if compute_path.exists():
        rows += list(compute_rows(json.loads(compute_path.read_text()), macro))
    return rows


def extra_analysis(result_rows, macro, price_map):
    settings = macro["valuation"]
    result = {"type": "one-variable sensitivities, not alternative measured forecasts",
              "frozen_capture_2029": {}, "required_2029_base": {}}
    compute = json.loads((BASE / "inputs/compute.json").read_text())
    for key, alternate in compute["sensitivity_2029_base_only"].items():
        one = copy.deepcopy(compute)
        one["companies"] = {key: copy.deepcopy(compute["companies"][key])}
        alt = copy.deepcopy(alternate)
        alt["case"] = "base"
        one["companies"][key]["forecasts"] = [alt]
        row = list(compute_rows(one, macro))[0]
        symbol = row["symbol"]
        result["frozen_capture_2029"][symbol] = valuation(
            row, price_map[symbol]["last"]["close"], settings["terminal_pe"][symbol], settings)
    for r in result_rows:
        if r["year"] != 2029 or r["case"] != "base":
            continue
        required_eps = r["price"] * (1 + settings["required_annual_return"]) ** r["discount_years"] / r["terminal_pe"]
        result["required_2029_base"][r["symbol"]] = {
            "required_eps_at_assumed_terminal_pe_for_12pct": required_eps,
            "base_eps": r["eps_quote_currency"],
            "required_eps_change_from_base": required_eps / r["eps_quote_currency"] - 1,
            "required_terminal_pe_with_base_eps": r["required_terminal_pe_for_12pct"],
        }
    # Required vendor capture for the entry-price test, holding all other base inputs fixed.
    for key in ("NVDA", "AVGO", "TSMC"):
        company = compute["companies"][key]
        r = next(x for x in company["forecasts"] if x["year"] == 2029 and x["case"] == "base")
        pool = r["eligible_pool_usd_bn"]
        multiplier = company["ordinary_shares_per_us_traded_unit"]
        shares = r["diluted_ordinary_shares_bn"]
        if key == "TSMC":
            coefficient = r["upstream_foundry_packaging_content_fraction"]
            slope = pool * r["TSMC_upstream_effective_capture"] * r["segments"][0]["operating_margin"] * (1 - r["tax_rate"]) / shares * multiplier
            symbol, variable = "TSM", "upstream_content_fraction"
        else:
            coefficient = (r["segments"][0]["pool_capture"] if key == "NVDA" else r["ai_combined_capture"])
            slope = pool * r["segments"][0]["operating_margin"] * (1 - r["tax_rate"]) / shares
            symbol, variable = key, "effective_vendor_capture"
        requested = result["required_2029_base"][symbol]
        requested["coefficient_name"] = variable
        requested["base_coefficient"] = coefficient
        requested["required_coefficient_all_else_fixed"] = coefficient + (
            requested["required_eps_at_assumed_terminal_pe_for_12pct"] - requested["base_eps"]) / slope
    kio = next(r for r in result_rows if r["symbol"] == "285A.T" and r["year"] == 2029 and r["case"] == "base")
    discount = (1 + settings["required_annual_return"]) ** kio["discount_years"]
    target_extra_value = max(0, kio["price"] - kio["conditional_entry_price"]) * discount
    result["kioxia_unvalued_assets_or_payout_threshold"] = {
        "status": "required incremental shareholder VALUE, NOT a forecast of cash or a claim that baseline cash is unvalued",
        "present_value_per_share_jpy": max(0, kio["price"] - kio["conditional_entry_price"]),
        "target_date_value_per_share_jpy": target_extra_value,
        "target_date_total_value_jpy_bn": target_extra_value * kio["diluted_shares_bn"],
        "caution": "Equity PE may already reflect cash/debt; earnings contain net financing income. Do not automatically add all cash. Only net additional value after deducting embedded after-tax interest capitalization is a valid sensitivity.",
        "cash_equivalent_if_incremental_cash_interest_already_in_eps": [
            {"assumed_cash_yield": yield_rate, "tax_rate": kio["tax_rate"],
             "cash_value_factor_after_deducting_capitalized_interest": 1 - kio["terminal_pe"] * yield_rate * (1 - kio["tax_rate"]),
             "required_target_date_cash_per_share_jpy": target_extra_value / (1 - kio["terminal_pe"] * yield_rate * (1 - kio["tax_rate"])),
             "required_target_date_cash_jpy_bn": target_extra_value / (1 - kio["terminal_pe"] * yield_rate * (1 - kio["tax_rate"])) * kio["diluted_shares_bn"]}
            for yield_rate in (0, 0.02, 0.04)
        ]
    }
    return result


def render_report(rows, notes, macro):
    report_path = BASE / "report.md"
    if not report_path.exists():
        return
    lookup = {(r["symbol"], r["year"], r["case"]): r for r in rows}

    def amount(value, symbol):
        return f"{value:,.0f}円" if symbol.endswith(".T") else f"${value:,.2f}"

    def eps(value, symbol):
        return f"{value:,.0f}" if symbol.endswith(".T") else f"{value:.2f}"

    def profit(row):
        value, currency = row["normal_net_income_bn"], row["financial_currency"]
        if currency == "JPY":
            return f"{value / 1000:.2f}兆円"
        suffix = "億ドル" if currency == "USD" else "億EUR"
        number = f"{value * 10:,.0f}" if value >= 10 else f"{value * 10:.1f}"
        return number + suffix

    base = ["|企業|10/16株価|2028年純利益|2029年純利益|2028年EPS|2029年EPS|現値÷29年EPS|",
            "|---|---:|---:|---:|---:|---:|---:|"]
    ranges = ["|企業|2028年EPS：弱／基準／強|2029年EPS：弱／基準／強|", "|---|---:|---:|"]
    values = ["|企業|2029仮定PER：弱／基準／強|基準2029末価格|年12%条件の入口価格|現値との差|基準EPSで必要な終点PER|",
              "|---|---:|---:|---:|---:|---:|"]
    rate_sensitivity = ["|企業|年8%条件|年12%条件|年16%条件|基準PER−25%|基準PER＋25%|",
                        "|---|---:|---:|---:|---:|---:|"]
    for symbol, name in NAMES.items():
        a, b = lookup[(symbol, 2028, "base")], lookup[(symbol, 2029, "base")]
        base.append(f"|{name}|{amount(b['price'],symbol)}|{profit(a)}|{profit(b)}|{eps(a['eps_quote_currency'],symbol)}|{eps(b['eps_quote_currency'],symbol)}|{b['forward_scenario_pe']:.1f}倍|")
        case_eps = lambda year: "／".join(eps(lookup[(symbol,year,c)]["eps_quote_currency"],symbol) for c in CASES)
        ranges.append(f"|{name}|{case_eps(2028)}|{case_eps(2029)}|")
        pes = "／".join(str(macro["valuation"]["terminal_pe"][symbol][c]) for c in CASES)
        values.append(f"|{name}|{pes}倍|{amount(b['terminal_price'],symbol)}|{amount(b['conditional_entry_price'],symbol)}|{b['entry_price_gap_pct']:+.0f}%|{b['required_terminal_pe_for_12pct']:.1f}倍|")
        rates = [amount(b["return_only_sensitivity"][str(r)], symbol) for r in (0.08,0.12,0.16)]
        pes_only = [amount(b["pe_only_sensitivity"][str(f)],symbol) for f in (0.75,1.25)]
        rate_sensitivity.append("|" + "|".join([name] + rates + pes_only) + "|")
    frozen = ["|企業|基準2029EPS|取り分/原価含量固定EPS|固定時の現値÷EPS|固定時の年12%入口価格|現値との差|",
              "|---|---:|---:|---:|---:|---:|"]
    for symbol, alternate in notes["frozen_capture_2029"].items():
        b = lookup[(symbol,2029,"base")]
        frozen.append(f"|{NAMES[symbol]}|{b['eps_quote_currency']:.2f}|{alternate['eps_quote_currency']:.2f}|{alternate['forward_scenario_pe']:.1f}倍|{amount(alternate['conditional_entry_price'],symbol)}|{alternate['entry_price_gap_pct']:+.0f}%|")
    document = report_path.read_text()
    for label, table in (("BASE",base),("RANGE",ranges),("VALUE",values),("FROZEN",frozen),("SENSITIVITY",rate_sensitivity)):
        pattern = re.compile(r"<!-- MODEL:" + label + r" -->.*?<!-- END:" + label + r" -->", re.S)
        replacement = "<!-- MODEL:" + label + " -->\n" + "\n".join(table) + "\n<!-- END:" + label + " -->"
        document, count = pattern.subn(lambda match: replacement, document)
        if count != 1:
            raise ValueError(("Missing report table marker", label, count))
    report_path.write_text(document, encoding="utf-8")


def build():
    macro = json.loads((BASE / "macro.json").read_text())
    quotes = json.loads((BASE / "prices.json").read_text())
    price_map = {r["symbol"]: r for r in quotes["items"]}
    result_rows = []
    for row in build_rows():
        symbol = row["symbol"]
        assert row["case"] in CASES and row["year"] in (2028, 2029)
        quote = price_map[symbol]
        assert quote["last"]["date"] == "2026-10-16"
        assert row["quote_currency"] == quote["currency"]
        result_rows.append(valuation(row, quote["last"]["close"],
                                     macro["valuation"]["terminal_pe"][symbol], macro["valuation"]))
    keys = [(r["symbol"], r["year"], r["case"]) for r in result_rows]
    assert len(keys) == len(set(keys))
    assert len(result_rows) == 48, "Expected eight companies, two years and three cases"
    out = {"as_of": macro["as_of"], "price_date": "2026-10-16",
           "status": "independent conditional scenarios, not guidance or consensus",
           "money_units": "billion financial currency; EPS in currency per quoted share",
           "dividends_tax_fx_change_in_returns": "excluded; ADR conversion uses fixed Oct16 FX",
           "required_annual_return": macro["valuation"]["required_annual_return"],
           "rows": result_rows}
    (BASE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    notes = extra_analysis(result_rows, macro, price_map)
    (BASE / "valuation-sensitivities.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    render_report(result_rows, notes, macro)
    fields = ["symbol", "year", "case", "financial_currency", "quote_currency",
              "revenue_bn", "operating_income_bn", "normal_net_income_bn", "diluted_shares_bn",
              "eps_financial_currency", "eps_quote_currency", "price", "forward_scenario_pe",
              "terminal_pe", "terminal_price", "conditional_entry_price", "entry_price_gap_pct",
              "required_terminal_pe_for_12pct", "annualized_price_return"]
    with (BASE / "results.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result_rows)
    for row in result_rows:
        if row["year"] == 2029 and row["case"] == "base":
            print(row["symbol"], "EPS", round(row["eps_quote_currency"], 3),
                  "PE", round(row["forward_scenario_pe"], 2),
                  "entry", round(row["conditional_entry_price"], 2),
                  "gap%", round(row["entry_price_gap_pct"], 1))


if __name__ == "__main__":
    build()
