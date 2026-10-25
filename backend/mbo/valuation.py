"""Deterministic, local-only DCF and illustrative LBO calculations.

No forecast probability or market financing terms are inferred here. Values are
JPY (not millions of JPY); output numbers are decimal strings. Missing inputs
are never replaced with zero. ``excess_cash`` must already exclude operating or
restricted cash. ``minimum_cash`` is an *additional* funded LBO cash reserve.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext


D = Decimal
JST = timezone(timedelta(hours=9))
FACTS = (
    'ebit', 'depreciation', 'capex', 'delta_nwc', 'excess_cash', 'debt',
    'noncontrolling_interest', 'shares_diluted',
)
PARAMS = (
    'revenue_growth', 'tax_rate', 'wacc', 'terminal_growth',
    'entry_debt_multiple', 'debt_interest', 'debt_amortization',
    'exit_multiple', 'target_irr', 'fee_rate', 'rollover_ratio', 'minimum_cash',
)
NAMES = ('bear', 'base', 'bull')


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('有限の十進数文字列が必要')
    if len(str(value)) > 128:
        raise ValueError('数値が長すぎる')
    try:
        result = D(value)
    except (InvalidOperation, ValueError):
        raise ValueError('有限の十進数文字列が必要') from None
    if (not result.is_finite() or abs(result) > D('1e30')
            or (result != 0 and abs(result) < D('1e-24'))):
        raise ValueError('数値が不正または計算範囲外')
    return result


def _text(value):
    if value is None:
        return None
    if value == 0:
        return '0'
    result = format(value, 'f')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def _moment(value, end_of_day=False):
    if not isinstance(value, str):
        raise ValueError('ISO形式の日付が必要')
    try:
        if len(value) == 10:
            day = date.fromisoformat(value)
            return datetime.combine(day, time.max if end_of_day else time.min, JST)
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.replace(tzinfo=JST) if result.tzinfo is None else result
    except ValueError:
        raise ValueError('ISO形式の日付が必要') from None


def _fact_metadata(facts, metric):
    fact = facts.get(metric)
    return fact if isinstance(fact, dict) else {}


def _fact_values(facts, cutoff):
    values, reasons = {}, []
    for metric in FACTS:
        fact = facts.get(metric)
        if not isinstance(fact, dict):
            reasons.append(f'{metric}: 必要な値が未入力')
            continue
        if fact.get('quality_status') != 'verified':
            reasons.append(f'{metric}: 原本確認が未完了')
        kind = fact.get('fact_kind')
        if kind is not None and kind != 'actual' and not (metric in ('excess_cash', 'shares_diluted') and kind == 'own_scenario'):
            reasons.append(f'{metric}: 実績以外の営業値は計算に使用しない')
        expected_unit = 'shares' if metric == 'shares_diluted' else 'JPY'
        if fact.get('unit') != expected_unit:
            reasons.append(f'{metric}: 単位は{expected_unit}で入力する')
        if metric != 'shares_diluted' and fact.get('currency') != 'JPY':
            reasons.append(f'{metric}: JPY以外の通貨または通貨未確認')
        for field in ('public_at', 'observed_at', 'ready_at', 'period_end'):
            if fact.get(field) is not None:
                try:
                    if _moment(fact[field]) > cutoff:
                        reasons.append(f'{metric}: {field}が評価時点より未来')
                except ValueError:
                    reasons.append(f'{metric}: {field}の日付が不正')
        try:
            value = _number(fact.get('value'))
            if value != value.to_integral_value():
                raise ValueError('JPY金額・株数は整数単位で入力する')
            if metric == 'shares_diluted' and value <= 0:
                raise ValueError('希薄化後株数は正値が必要')
            if metric not in ('ebit', 'delta_nwc') and value < 0:
                raise ValueError('負値は使用できない')
            values[metric] = value
        except ValueError as exc:
            reasons.append(f'{metric}: {exc}')
    shares = facts.get('shares_diluted', {})
    if not isinstance(shares, dict) or not shares.get('share_basis'):
        reasons.append('shares_diluted: 株式分割基準が未確認')
    bridge_dates = {facts[k].get('period_end') for k in ('excess_cash', 'debt', 'noncontrolling_interest')
                    if isinstance(facts.get(k), dict) and facts[k].get('period_end')}
    if len(bridge_dates) > 1:
        reasons.append('現金・負債・非支配持分のBS基準日が不一致')
    cash = facts.get('cash_and_equivalents')
    if _fact_metadata(facts, 'excess_cash').get('fact_kind') == 'own_scenario':
        if not isinstance(cash, dict) or cash.get('quality_status') != 'verified' or cash.get('fact_kind') != 'actual':
            reasons.append('余剰現金の独自仮定には同じBS日の確認済み現金実績が必要')
        else:
            try:
                total_cash = _number(cash.get('value'))
                if cash.get('unit') != 'JPY' or cash.get('currency') != 'JPY' or total_cash < 0:
                    raise ValueError()
                if not cash.get('period_end') or cash['period_end'] != facts['excess_cash'].get('period_end'):
                    reasons.append('現金実績と独自余剰現金のBS基準日が不一致')
                if values.get('excess_cash', D(0)) > total_cash:
                    reasons.append('独自余剰現金が確認済み現金実績を超える')
                for field in ('public_at', 'observed_at', 'ready_at', 'period_end'):
                    if cash.get(field) is not None and _moment(cash[field]) > cutoff:
                        reasons.append(f'cash_and_equivalents: {field}が評価時点より未来')
            except ValueError:
                reasons.append('現金実績の単位・金額・日付が未確認')
    return values, reasons


def _scenario(raw):
    result, reasons = {}, []
    if not isinstance(raw, dict):
        return {}, ['シナリオが未入力']
    years = raw.get('horizon_years')
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 30:
        reasons.append('horizon_years: 1〜30の整数が必要')
    else:
        result['horizon_years'] = years
    for key in PARAMS:
        try:
            result[key] = _number(raw.get(key))
        except ValueError as exc:
            reasons.append(f'{key}: {exc}')
    if reasons:
        return result, reasons
    if not D('-1') < result['revenue_growth'] <= D('1'):
        reasons.append('revenue_growth: -1より大きく1以下が必要')
    for key in ('tax_rate', 'debt_amortization', 'fee_rate'):
        if not 0 <= result[key] <= 1:
            reasons.append(f'{key}: 0〜1が必要')
    if not 0 <= result['rollover_ratio'] < 1:
        reasons.append('rollover_ratio: 0以上1未満が必要')
    if not 0 < result['wacc'] <= 1 or result['terminal_growth'] <= -1:
        reasons.append('wacc/terminal_growth: 割引・成長条件が不正')
    if result['wacc'] <= result['terminal_growth']:
        reasons.append('wacc: terminal_growthより大きい必要がある')
    if not 0 < result['target_irr'] <= 1:
        reasons.append('target_irr: 0より大きく1以下が必要')
    for key in ('entry_debt_multiple', 'debt_interest', 'exit_multiple', 'minimum_cash'):
        if result[key] < 0:
            reasons.append(f'{key}: 負値は使用できない')
    if result['exit_multiple'] == 0:
        reasons.append('exit_multiple: 正値が必要')
    if result['minimum_cash'] != result['minimum_cash'].to_integral_value():
        reasons.append('minimum_cash: JPY整数単位が必要')
    return result, reasons


def _assumptions(params):
    return {key: value if isinstance(value, int) else _text(value)
            for key, value in params.items()}


def _operations(facts, scenario, year):
    growth = (1 + scenario['revenue_growth']) ** year
    result = {key: facts[key] * growth
              for key in ('ebit', 'depreciation', 'capex', 'delta_nwc')}
    # A one-year release is not assumed to recur forever. The reported signed
    # amount remains intact in facts; only the forward scenario clips releases.
    result['delta_nwc'] = max(result['delta_nwc'], D(0))
    # A low investment year is not assumed to avoid replacement indefinitely.
    # This is an explicit conservative forecast policy, not a restated actual.
    result['capex'] = max(result['capex'], result['depreciation'])
    return result


def _dcf(facts, scenario):
    yearly, value = [], D(0)
    for year in range(1, scenario['horizon_years'] + 1):
        op = _operations(facts, scenario, year)
        # No immediate tax refund is assumed for operating losses.
        taxes = max(op['ebit'], D(0)) * scenario['tax_rate']
        fcff = op['ebit'] - taxes + op['depreciation'] - op['capex'] - op['delta_nwc']
        pv = fcff / (1 + scenario['wacc']) ** year
        value += pv
        yearly.append({'year': year, **{k: _text(v) for k, v in op.items()},
                       'taxes': _text(taxes), 'fcff': _text(fcff), 'present_value': _text(pv)})
    terminal = fcff * (1 + scenario['terminal_growth']) / (scenario['wacc'] - scenario['terminal_growth'])
    value += terminal / (1 + scenario['wacc']) ** scenario['horizon_years']
    equity = value + facts['excess_cash'] - facts['debt'] - facts['noncontrolling_interest']
    return value, equity, yearly


def _lbo(facts, scenario):
    assumptions = _assumptions(scenario)
    assumptions.update({
        'scenario': 'base',
        'financing': '独自の固定借入仮定。融資承諾・市場条件・買付価格の予測ではない',
        'debt_amortization_basis': '初期借入元本に対する年率。追加借入・任意返済なし',
        'cash_policy': '余剰CFは無利息で留保し、出口で全額分配。途中配当なし',
        'minimum_cash_policy': 'excess_cashは既に運転必要額控除後。minimum_cashは追加積立で、買収使途と出口現金に各1回計上',
        'rollover_policy': '株式取得対価×rollover_ratioを再出資。スポンサーと同順位・出資額比例で出口分配',
        'fee_basis': '株式取得対価×fee_rate。借換え等の追加費用は別途未モデル化',
        'tax_policy': '正の利払い後利益にのみ税率適用。税損失の還付・繰越は仮定しない',
        'lease_policy': '入力済みCFとdebtのリース処理が整合していることが前提',
        'growth_basis': '営業値は同率成長。将来の運転資本減少は0、設備投資は少なくとも減価償却額とする独自仮定',
    })
    result = {'status': 'pending', 'max_price_per_share': None,
              'assumptions': assumptions, 'reasons': [], 'yearly': []}
    if facts['noncontrolling_interest'] != 0:
        result['reasons'] = ['非支配持分あり: 親会社へのCF帰属と出口配分の追加確認が必要']
        return result
    ebitda = facts['ebit'] + facts['depreciation']
    if ebitda <= 0:
        result.update(status='infeasible', reasons=['初期EBITDAが0以下のため、この借入モデルは適用できない'])
        return result
    initial_debt = ebitda * scenario['entry_debt_multiple']
    debt, cash = initial_debt, scenario['minimum_cash']
    for year in range(1, scenario['horizon_years'] + 1):
        op = _operations(facts, scenario, year)
        interest = debt * scenario['debt_interest']
        tax = max(op['ebit'] - interest, D(0)) * scenario['tax_rate']
        available = op['ebit'] + op['depreciation'] - op['capex'] - op['delta_nwc'] - interest - tax
        repayment = min(debt, initial_debt * scenario['debt_amortization'])
        closing_cash = cash + available - repayment
        closing_debt = debt - repayment
        result['yearly'].append({
            'year': year, **{k: _text(v) for k, v in op.items()},
            'opening_debt': _text(debt), 'interest': _text(interest), 'taxes': _text(tax),
            'cash_before_repayment': _text(available), 'repayment': _text(repayment),
            'closing_debt': _text(closing_debt), 'closing_cash': _text(closing_cash),
        })
        if closing_cash < scenario['minimum_cash']:
            result.update(status='infeasible', reasons=[f'{year}年目: 返済後の最低現金を維持できない（追加出資なしの仮定）'])
            return result
        debt, cash = closing_debt, closing_cash
    exit_ev = (op['ebit'] + op['depreciation']) * scenario['exit_multiple']
    exit_equity = exit_ev - debt + cash
    if exit_equity <= 0:
        result.update(status='infeasible', reasons=['出口の株主価値が0以下'])
        return result

    def financing(purchase):
        fees = purchase * scenario['fee_rate']
        rollover = purchase * scenario['rollover_ratio']
        uses = purchase + facts['debt'] + fees + scenario['minimum_cash']
        sponsor = uses - initial_debt - facts['excess_cash'] - rollover
        total_equity = sponsor + rollover
        return fees, rollover, uses, sponsor, total_equity

    def affordable(purchase):
        _, _, _, sponsor, equity = financing(purchase)
        if sponsor <= 0 or equity <= 0:
            return None
        distribution = exit_equity * sponsor / equity
        return distribution / (1 + scenario['target_irr']) ** scenario['horizon_years'] - sponsor

    # The lower bound excludes zero/negative sponsor funding with a fixed loan.
    offset = initial_debt + facts['excess_cash'] - facts['debt'] - scenario['minimum_cash']
    lower = max(D(0), offset / (1 - scenario['rollover_ratio'] + scenario['fee_rate'])) + D('0.000001')
    lower_npv = affordable(lower)
    if lower_npv is None or lower_npv < 0:
        result.update(status='infeasible', reasons=['固定借入・再出資・要求IRRの組合せで正のスポンサー出資が成立しない'])
        return result
    upper = max(D(1), lower * 2)
    for _ in range(200):
        if affordable(upper) < 0:
            break
        upper *= 2
    else:
        result['reasons'] = ['価格探索の上限に到達']
        return result
    for _ in range(180):
        mid = (lower + upper) / 2
        if affordable(mid) >= 0:
            lower = mid
        else:
            upper = mid
    purchase = lower
    fees, rollover, uses, sponsor, equity = financing(purchase)
    sponsor_exit = exit_equity * sponsor / equity
    result.update(status='ok', max_price_per_share=_text(purchase / facts['shares_diluted']))
    result['financing'] = {
        'purchase_equity_value': _text(purchase), 'existing_debt_refinanced': _text(facts['debt']),
        'fees': _text(fees), 'additional_cash_reserve': _text(scenario['minimum_cash']),
        'total_uses': _text(uses), 'new_debt': _text(initial_debt),
        'excess_cash_used': _text(facts['excess_cash']), 'rollover_equity': _text(rollover),
        'sponsor_equity': _text(sponsor), 'sponsor_ownership': _text(sponsor / equity),
        'total_sources': _text(initial_debt + facts['excess_cash'] + rollover + sponsor),
        'exit_enterprise_value': _text(exit_ev), 'exit_equity_value': _text(exit_equity),
        'sponsor_exit_proceeds': _text(sponsor_exit),
        'sponsor_npv_at_target_irr': _text(affordable(purchase)),
    }
    return result


def _discount(price, facts, cutoff, base):
    result = {'status': 'pending', 'value': None, 'reasons': []}
    if not isinstance(price, dict):
        result['reasons'] = ['価格未入力']
        return result
    reasons = result['reasons']
    try:
        amount = _number(price.get('value'))
        if amount <= 0:
            reasons.append('株価は正値が必要')
    except ValueError as exc:
        amount = None
        reasons.append(f'株価: {exc}')
    if price.get('quality_status') != 'verified':
        reasons.append('株価の確認が未完了')
    if price.get('currency') != 'JPY':
        reasons.append('株価の通貨がJPYではない')
    shares = facts.get('shares_diluted', {})
    basis = shares.get('share_basis') if isinstance(shares, dict) else None
    if not basis or price.get('share_basis') != basis:
        reasons.append('株価と株数の分割基準が一致しない')
    try:
        when = _moment(price.get('price_at'))
        if when > cutoff:
            reasons.append('株価日が評価時点より未来')
        elif (cutoff.astimezone(JST).date() - when.astimezone(JST).date()).days > 14:
            reasons.append('株価が14日より古い')
    except ValueError:
        reasons.append('株価日が不正または未入力')
    if base and base['status'] == 'infeasible':
        reasons.append('基準シナリオに正の残余株主価値がないため、割安率は算出できない')
    elif not base or base['status'] != 'ok':
        reasons.append('基準シナリオの価値が未計算')
    elif D(base['value_per_share']) <= 0:
        reasons.append('基準シナリオの1株価値が0以下')
    if not reasons:
        result.update(status='ok', value=_text(1 - amount / D(base['value_per_share'])))
    return result


def evaluate(facts: dict[str, dict], scenarios: list[dict], price: dict | None, as_of: str) -> dict:
    """Return JSON-safe values; invalid/missing evidence yields pending, not zero.

    Scenario amounts and rates must be explicit; growth applies equally to EBIT,
    depreciation, capex and delta working capital. LBO uses the base scenario.
    """
    with localcontext() as context:
        context.prec = 48
        return _evaluate(facts, scenarios, price, as_of)


def _evaluate(facts, scenarios, price, as_of):
    common = []
    try:
        cutoff = _moment(as_of, end_of_day=True)
    except ValueError as exc:
        cutoff = datetime.min.replace(tzinfo=JST)
        common.append(f'as_of: {exc}')
    facts = facts if isinstance(facts, dict) else {}
    values, fact_reasons = _fact_values(facts, cutoff)
    common.extend(fact_reasons)
    scenarios = scenarios if isinstance(scenarios, list) else []
    rows, parsed = [], {}
    for name in NAMES:
        matches = [s for s in scenarios if isinstance(s, dict) and s.get('name') == name]
        params, reasons = _scenario(matches[0] if matches else None)
        if len(matches) > 1:
            reasons.append(f'{name}: シナリオが重複')
        row = {'name': name, 'status': 'pending', 'value_per_share': None,
               'equity_value': None, 'enterprise_value': None,
               'assumptions': _assumptions(params), 'reasons': common + reasons, 'yearly': []}
        row['assumptions'].update({
            'fcf_basis': 'FCFF（利払い前）。営業CF−設備投資の一次選別proxyとは別',
            'growth_basis': '営業値は同率成長。将来の運転資本減少は0、設備投資は少なくとも減価償却額とする独自仮定。実績値は変更しない',
            'tax_policy': '赤字による即時税還付は仮定しない',
            'equity_bridge': '事業価値+余剰現金−負債−非支配持分。' +
                            ('余剰現金は会社実績ではなく運転必要額控除後の独自仮定。' if _fact_metadata(facts, 'excess_cash').get('fact_kind') == 'own_scenario' else '') +
                            ('株数は公表済み自己株増減を反映した独自推計。' if _fact_metadata(facts, 'shares_diluted').get('fact_kind') == 'own_scenario' else '') +
                            'その他資産・リースは入力に明記した範囲',
        })
        if not row['reasons']:
            ev, equity, yearly = _dcf(values, params)
            row.update(enterprise_value=_text(ev), equity_value=_text(equity), yearly=yearly)
            if equity <= 0:
                row.update(status='infeasible', reasons=[
                    '試算上の残余株主価値が0以下のため、正の1株価値は算出できない'])
            else:
                row.update(status='ok', value_per_share=_text(equity / values['shares_diluted']))
            parsed[name] = params
        rows.append(row)
    base = next(row for row in rows if row['name'] == 'base')
    lbo = (_lbo(values, parsed['base']) if 'base' in parsed else
           {'status': 'pending', 'max_price_per_share': None, 'assumptions': {},
            'reasons': base['reasons'][:], 'yearly': []})
    return {
        'standalone': {'status': 'ok' if all(row['status'] == 'ok' for row in rows) else 'pending',
                       'scenarios': rows},
        'discount_to_base': _discount(price, facts, cutoff, base),
        'lbo': lbo,
    }
