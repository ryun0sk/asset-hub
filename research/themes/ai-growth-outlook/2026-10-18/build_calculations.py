"""Reproduce illustrative sensitivities, not company forecasts. No network access."""
import json
from pathlib import Path


def build():
    stock_cases = []
    for growth, entry_pe, exit_pe in [(0.20, 40, 25), (0.20, 50, 25), (0.25, 40, 25)]:
        eps_factor = (1 + growth) ** 3
        price_factor = eps_factor * exit_pe / entry_pe
        stock_cases.append({
            "assumptions": {"years": 3, "annual_eps_growth": growth,
                            "entry_pe": entry_pe, "exit_pe": exit_pe},
            "eps_factor": round(eps_factor, 6),
            "share_price_return_ex_dividends_fx": round(price_factor - 1, 6),
        })
    # Arbitrary units. Unit cost includes production costs only; not an OP model.
    before = {"volume": 100, "asp": 100, "unit_production_cost": 60}
    after = {"volume": 120, "asp": 80, "unit_production_cost": 55}
    for row in (before, after):
        row["revenue"] = row["volume"] * row["asp"]
        row["gross_profit"] = row["volume"] * (row["asp"] - row["unit_production_cost"])
    return {
        "as_of": "2026-10-18", "type": "independent_hypothetical_sensitivity",
        "warning": "No company price targets, growth forecasts, probabilities or current market prices.",
        "formula": "share price factor = EPS factor * exit PER / entry PER; excludes dividends and FX",
        "stock_cases": stock_cases,
        "commodity_example": {
            "type": "arbitrary_units_not_kioxia_forecast", "before": before, "after": after,
            "volume_growth": after["volume"] / before["volume"] - 1,
            "gross_profit_growth": after["gross_profit"] / before["gross_profit"] - 1,
        },
        "arista_gaap_operating_profit_growth_q2_2026": {
            "type": "calculation_from_company_actuals", "unit": "USD million",
            "current": 1378.0, "prior": 986.2,
            "growth": round(1378.0 / 986.2 - 1, 6),
            "source": "https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Second-Quarter-2026-Financial-Results/default.aspx",
            "published": "2026-08-04",
        },
        "asml_q3_2026": {
            "type": "calculation_from_company_actuals", "unit": "EUR billion",
            "revenue_current": 11.662, "revenue_prior": 7.516,
            "revenue_growth": round(11.662 / 7.516 - 1, 6),
            "operating_profit_current": 5.173, "operating_profit_prior": 2.468,
            "operating_profit_growth": round(5.173 / 2.468 - 1, 6),
            "operating_margin": round(5.173 / 11.662, 6),
            "source": "https://investor.asml.com/static-files/d310262b-d037-485d-83b5-92c93cc462f0",
            "published": "2026-10-14",
        },
    }


if __name__ == "__main__":
    destination = Path(__file__).with_name("calculations.json")
    destination.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)
