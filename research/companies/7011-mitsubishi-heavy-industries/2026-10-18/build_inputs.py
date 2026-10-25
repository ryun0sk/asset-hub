"""Build verified MHI EPS inputs from the official reports saved alongside this file."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

ROOT = Path(__file__).resolve().parent
# Fiscal year labels follow MHI: FY2025 ends in March 2026.
# period end, publication date, diluted cumulative EPS, report identifier, fiscal label
ROWS = [
    ('2023-12-31', '2024-02-06', '41.059', 'fy20233q', '2024年3月期9か月累計'),
    ('2024-03-31', '2024-05-08', '66.04', 'fy20234q', '2024年3月期通期'),
    ('2024-06-30', '2024-08-06', '18.52', 'fy20241q', '2025年3月期第1四半期'),
    ('2024-09-30', '2024-11-05', '31.85', 'fy20242q', '2025年3月期中間期'),
    ('2024-12-31', '2025-02-04', '51.19', 'fy20243q', '2025年3月期9か月累計'),
    ('2025-03-31', '2025-05-09', '73.02', 'fy20244q', '2025年3月期通期'),
    ('2025-06-30', '2025-08-05', '20.31', 'fy20251q', '2026年3月期第1四半期'),
    ('2025-09-30', '2025-11-07', '34.20', 'fy20252q', '2026年3月期中間期'),
    ('2025-12-31', '2026-02-04', '62.79', 'fy20253q', '2026年3月期9か月累計'),
    ('2026-03-31', '2026-05-12', '98.84', 'fy20254q', '2026年3月期通期'),
    ('2026-06-30', '2026-08-04', '40.07', 'fy20261q', '2027年3月期第1四半期'),
]


def rounded(value):
    return float(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def url(key):
    return f'https://www.mhi.com/jp/finance/library/result/pdf/{key}/kessan_tansin.pdf'


def record(row):
    end, published, eps, key, _ = row
    return dict(periodEnd=end, publishedDate=published, knownFrom=published,
                eps=float(eps), source=url(key))


quarterly = []
for previous, row in zip(ROWS, ROWS[1:]):
    current = record(row)
    value = Decimal(row[2])
    if row[0][5:] == '06-30':
        method = '会社公表の第1四半期希薄化後EPS'
    else:
        value -= Decimal(previous[2])
        method = f'累計差分による概算: {row[2]} - {previous[2]}'
        current['componentSources'] = [url(previous[3]), url(row[3])]
    current.update(eps=rounded(value), method=method)
    quarterly.append(current)

annual = [record(row) for row in ROWS if row[0].endswith('03-31')]
ttm = []
for i in range(3, len(quarterly)):
    window = quarterly[i-3:i+1]
    latest = window[-1]
    first_year, first_month, _ = map(int, window[0]['periodEnd'].split('-'))
    start_month = first_month-2
    entry = {k: latest[k] for k in ['periodEnd', 'publishedDate', 'knownFrom', 'source']}
    entry.update(eps=rounded(sum(Decimal(str(q['eps'])) for q in window)),
                 profitPeriodStart=f'{first_year:04}-{start_month:02}-01',
                 halfYearAnnualizedEps=rounded(2 * sum(Decimal(str(q['eps'])) for q in window[-2:])),
                 method='独自概算: 直近4四半期の希薄化後EPS合算。半年年換算は直近2四半期合計×2。',
                 componentSources=list(dict.fromkeys(q['source'] for q in window)))
    ttm.append(entry)

sources = []
for row in ROWS:
    path = ROOT/'sources'/f'{row[3]}-kessan-tansin.pdf'
    sources.append(dict(url=url(row[3]), publishedDate=row[1],
                        title=f'三菱重工 {row[4]} 決算短信',
                        localPath=f'sources/{path.name}', sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
sources += [
    dict(url='https://www.mhi.com/jp/finance', publishedDate='2026-10-16', title='三菱重工IR情報: 次回決算予定'),
    dict(url='https://www.mhi.com/jp/finance/library/result_archive', publishedDate=None, title='決算短信アーカイブ・2024年3月期資料訂正に関する注記'),
]
data = dict(
    symbol='7011.T', name='三菱重工', currency='JPY', code='7011',
    basis='IFRS連結・希薄化後実績EPS（継続事業と非継続事業の合算）。単独四半期は第1四半期以外を累計EPSの差分で概算。',
    splitBasis='2024年4月1日の1株→10株の株式分割後基準。2023年12月期累計EPS410.59円は10で割り41.059円へ換算。',
    notes=[
        '株価の分割調整基準をEPSに合わせる。会社予想は基本EPS、実績は希薄化後EPSであり基準差を明記する。',
        'EPS差分には期間ごとの加重平均株式数、希薄化効果、丸めの差があるため、単独四半期・TTM・半年年換算は会社の公式EPSではなく概算。',
        'knownFromは終値比較に用いる日付。場中13:30の決算公表を当日から反映。月初・月末比較では公表当日/翌営業日の差は生じない。',
        '2025年9月期以降ロジスネクストを非継続事業に分類しているが、本系列は継続・非継続を合算する親会社帰属利益のEPSを一貫して使用。',
        '固定資産売却、金融収益、非継続事業などの一時的な損益を調整していない全社実績。ガスタービン事業だけのEPSではない。',
        '半年年換算は直近2四半期の機械的な年換算で、会社予想ではない。案件進捗・利益認識の季節性や一時利益によりTTMとの差が拡大する。',
        '2024年3月期短信は会社ウェブサイト公開分に誤りがあり訂正済み。会社説明では当初TDnet開示資料は正しい。本保存は訂正版。',
    ],
    quarterly=quarterly, annual=annual, ttm=ttm,
    cumulative=[record(row) for row in ROWS],
    companyForecast=dict(eps=113.09, periodEnd='2027-03-31', announced='2026-08-04', source=url('fy20261q')),
    companyForecastNote='2027年3月期の会社予想基本EPS113.09円（8月4日短信再掲、業績予想修正なし）。実績の希薄化後EPSとは基準が異なる。外部予想ではない。',
    analyst=None,
    nextEarnings=dict(date='2026-11-06', time='13:30', timezone='Asia/Tokyo', source='https://www.mhi.com/jp/finance'),
    sources=sources,
)
assert rounded(sum(Decimal(str(q['eps'])) for q in quarterly[1:5])) == 73.02
assert rounded(sum(Decimal(str(q['eps'])) for q in quarterly[5:9])) == 98.84
assert ttm[-1]['eps'] == 118.60
assert ttm[-1]['halfYearAnnualizedEps'] == 152.24
(ROOT/'eps-inputs.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: data[k] for k in ['symbol','companyForecast','nextEarnings']},ensure_ascii=False))
print('latest TTM', ttm[-1])
