"""Purely hypothetical top-down arithmetic; no company forecast or market feed."""
import json
from pathlib import Path


def component_case(annual_budget_trillion_jpy, allocation, revenue_share, net_margin):
    market = annual_budget_trillion_jpy * allocation
    revenue = market * revenue_share
    profit = revenue * net_margin
    return {
        "year": 2040,
        "annual_budget_trillion_jpy": annual_budget_trillion_jpy,
        "component_purchase_allocation": allocation,
        "company_value_share_in_same_component_market": revenue_share,
        "normal_attributable_net_margin_assumption": net_margin,
        "component_market_trillion_jpy": round(market, 8),
        "company_ai_revenue_trillion_jpy": round(revenue, 8),
        "company_ai_net_profit_trillion_jpy": round(profit, 8),
        "company_ai_net_profit_oku_jpy": round(profit * 10000, 4),
    }


def required_net_profit(current_market_cap, years, annual_return, terminal_pe, share_count_factor=1):
    """Same currency; assumes no dividends or FX effects. PE must be positive."""
    if terminal_pe <= 0 or share_count_factor <= 0 or years < 0 or annual_return <= -1:
        raise ValueError("Invalid valuation assumptions")
    return current_market_cap * (1 + annual_return) ** years * share_count_factor / terminal_pe


if __name__ == "__main__":
    result = {
        "as_of": "2026-10-18 JST",
        "type": "hypothetical_method_example_not_company_forecast",
        "currency": "JPY, illustrative nominal target-year basis",
        "input_warning": "800 trillion is Son's stated long-term scenario; all allocation/share/margin inputs are arbitrary illustrative assumptions, not verified company data.",
        "son_scenario_source": "https://www.softbank.jp/business/content/blog/202607/sbw2026-softbank-son-main-keynote",
        "cases": [component_case(800, .03, .20, .15), component_case(800, .03, .20, .05)],
        "required_profit_formula": "V0*(1+r)**n*(future_shares/current_shares)/terminal_PE; excludes dividends and FX",
        "not_included": ["current company valuations", "actual company market shares", "non-AI profits", "2028/2029 forecasts", "discounted cash-flow valuation"],
    }
    destination = Path(__file__).with_name("gdp-share-calculations.json")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)
