# 装置・材料・テスト14社の再確認（2026年11月6日）

株価はrootで取得。金額は各社現地通貨の十億、EPSは普通株1株。実績・会社予想・独自試算を区別する。

| 銘柄 | 確認状態 | 最新の利益情報 | 前回からの変化・評価の焦点 |
|---|---|---|---|
| 信越化学 (4063.T) | confirmed | FY2027/3 H1 実績NI 286.939 / 会社予想NI 525 | H1営業利益+15.6%、電子材料OP+28%。7月の通期純利益525bn/EPS286円は据置。AI材料好調をPVC全体へ延長しない。 |
| SUMCO (3436.T) | pending_report | FY2026/12 H1; Q3未発表 実績NI -12.895 / 会社予想NI -12.8 | 11/6時点でQ3未公表。会社8/6予想はQ3単独営業損益ほぼ均衡、9M純損失12.8bn。11/11予定を外部カレンダーで確認。 |
| GlobalWafers (6488.TWO) | confirmed | CY2026 Q3 実績NI 未抽出 / 会社予想NI 未公表・四半期のみ | Q3利益/EPS公表へ更新。Q2投資評価益の高い比較基準と伊8インチ工場火災の影響。11/3にMicron向け最大US$500m・10年CB案（年0.5%）を承認。 |
| Siltronic (WAF.DE) | confirmed | CY2026 Q3 and 9M 実績NI -0.1849 / 会社予想NI 未公表・四半期のみ | 売上見通しを前年並みへ上方、EBITDA率22〜24%へ絞る。数量は回復したが新設償却で9M EBIT赤字。 |
| 東京エレクトロン (8035.T) | confirmed | FY2027/3 H1 実績NI 376.929 / 会社予想NI 865 | 前回はH1予想のみ。10/30に通期NI865bn/EPS381.69円を公表、H1も7月予想349bnを上回る。 |
| Lam Research (LRCX) | confirmed | FY2027 Q1 ended 2026-09-27 実績NI 2.753138 / 会社予想NI 未公表・四半期のみ | 9月期売上+22%QoQ、GAAP EPS2.19、12月期売上中心8.6bn/EPS2.33へ。AI装置需要が強い。 |
| ASE Technology (3711.TW) | confirmed | CY2026 Q3 実績NI 26.996438 / 会社予想NI 未公表・四半期のみ | 前回はQ3売上速報のみ。正式利益はNI26.996bn、OP33.142bnと強い。ATM営業利益率20.0%（Q2 15.7%）、営業外差引は損失で前四半期の為替・投資益依存が低下。 |
| 味の素 (2802.T) | pending_report | FY2027/3 Q1; H1 scheduled 2026-11-09 実績NI 36.452 / 会社予想NI 123.5 | 11/6時点Q2決算未発表、11/9予定。ABF強いが全社は食品・バイオ等を含む。 |
| イビデン (4062.T) | confirmed | FY2027/3 H1 実績NI 38.574 / 会社予想NI 89 | 通期NI84→89bn、EPS149.68→157.17円へ上方。10/29の追加150bn投資はFY2029下期立上げ、利益寄与FY2030以降の説明。 |
| Unimicron (3037.TW) | limited | CY2026 9M 実績NI 28.209851 / 会社予想NI 未公表・四半期のみ | 9M会社開示を転載本文で確認。Q3売上速報52.65bnから正式9M利益まで更新。ただし原ホスト財務報告を直接取得できず確認限定。 |
| ディスコ (6146.T) | confirmed | FY2027/3 H1 実績NI 80.366 / 会社予想NI 121.9 | 前回の個別出荷速報からH1正式決算へ更新。H1NI+43.7%。通期ではなく9Mまでの会社予想に注意。 |
| Teradyne (TER) | confirmed | CY2026 Q3 ended 2026-09-27 実績NI 0.3424 / 会社予想NI 未公表・四半期のみ | Q3は売上ガイダンス上限を超え、前年比70%増。Q4売上1.25〜1.35bnでQ3付近、GAAP EPS1.88〜2.18。 |
| ASML (ASML) | confirmed | CY2026 Q3 実績NI 4.9604 / 会社予想NI 未公表・四半期のみ | 10/18以降の新決算ではなく10/14Q3を再確認。2027〜28供給不足見込み、28年能力増検討。Q3純利益に税前EUR509.7m評価益が含まれる。 |
| アドバンテスト (6857.T) | confirmed | FY2027/3 H1 (company FY2026) 実績NI 368.083 / 会社予想NI 741.5 | 通期NI660→741.5bn/EPS1027.08へ上方。AI半導体数量・テスト複雑化を反映。ただしH1金融収益約57bnは主に投資評価益。 |

## 深掘り候補と利益の持続性

東京エレクトロン、アドバンテスト、ASEを優先する。会社予想/現在の四半期利益を起点に、1〜2年の数量・利益率変化を明示した条件付き試算をJSONへ保存した。購入順位は株価を結合するroot側で判断する。

- TEL：FY2027/3会社NI865bn・基本EPS381.69円。FY2028/3独自NI794〜1084bn、中心約964bn。正常化評価555〜794bn。売上の0〜20%増と営業利益率29〜33%、税26%を仮定。
- アドバンテスト：会社NI741.5bnには主に投資評価益を含む金融収益の寄与。全金融収益57bnを除き税率27%を仮定する慎重代理ではNI約699.9bn、EPS約969.4円。FY2028/3独自NI653〜881bn。報告EPSの単純年換算から算出しない。
- ASE：Q3のATM採算改善が強く、営業外差引損失でもNIが増加。CY2027独自NI100〜150bn、中心125bn。営業外益を戻さず売上1.0〜1.15兆TWD、OP率13〜16%、税16%、NCI4bnを仮定。

ASMLは質の高い比較候補だが、EUR EPSとUSD株価の換算が必要。Q3に税前0.5097bn EURの投資益。税率16.7%仮定の代理ではQ3希薄化EPS約11.82 EUR、単純年換算約47.3 EUR。これは通期予想でもTTMでもない。

## 注意点

- イビデンの追加150bn投資はFY2029下期立上げ、業績貢献FY2030以降。2027〜28の利益へ即加算しない。
- 味の素Q2は11月9日、SUMCO Q3は11月11日予定。11月6日13時台に未発表分を埋めない。
- GlobalWafersのQ2はSiltronic評価益、Q3はイタリア工場火災と新設償却。11月3日Micron向けCB案で追加希薄化を要確認。
- Siltronicは売上回復とEBITDA改善があっても、償却後の純利益は赤字。低PBRだけで割安としない。
- UnimicronはMOPS会社公告の転載本文を確認したが原ホスト資料未取得。9M税前利益35.04bnに対しOP19.94bnで、営業外益の正常化が不可欠。

## 出典

### 信越化学
- 2026-10-27 [H1 consolidated results](https://www.shinetsu.co.jp/wp-content/uploads/2026/07/20261027_con_E.pdf)

### SUMCO
- 2026-08-06 [H1 company financial results](https://ssl4.eir-parts.net/doc/3436/tdnet/2864809/00.pdf)
- 2026-11-06 accessed [IR calendar](https://www.sumcosi.com/english/ir/event/calendar.html)
- 2026-11-06 accessed [External Q3 scheduled November 11](https://kabuyoho.jp/sp/report?bcode=3436)

### GlobalWafers
- 2026-11-03 [Q3 results release](https://www.sas-globalwafers.com/en/globalwafers-reports-q3-2026-results/)
- 2026-11-03 [Micron private convertible-bond proposal](https://www.sas-globalwafers.com/en/gwc_news_en_20261103-1/)

### Siltronic
- 2026-11-04 [Q3 company release](https://www.siltronic.com/en/press/press-releases/siltronic-slightly-raises-sales-guidance-for-2026-higher-demand-drives-volume-development-in-q3-2026.html)

### 東京エレクトロン
- 2026-10-30 [H1 and full-year forecast](https://www.tel.com/ir/library/report/i61j9u00000000gf-att/fy27q2tanshin-e.pdf)

### Lam Research
- 2026-10-21 [September quarter results and December guidance](https://investor.lamresearch.com/2026-10-21-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-September-27%2C-2026)
- 2026-10-22 [SEC 10-Q](https://www.sec.gov/Archives/edgar/data/707549/000070754926000054/lrcx-20260927.htm)

### ASE Technology
- 2026-10-29 [SEC company Q3 financial release](https://www.sec.gov/Archives/edgar/data/1122411/000095010326016324/dp255760_6k.htm)
- 2026-10-29 [SEC company Q3 presentation](https://www.sec.gov/Archives/edgar/data/1122411/000095010326016323/dp255782_6k.htm)

### 味の素
- 2026-08-06 [Q1 financial results](https://www.ajinomoto.co.jp/company/en/ir/event/presentation/main/011111113/teaserItems1/01/linkList/0/link/FY26Q1_Tanshin_E.pdf)
- 2026-11-06 accessed [IR November 9 Q2 results event](https://ajinomoto-ir.swcms.net/company/en/ir.html)

### イビデン
- 2026-10-29 [H1 financial results and forecast](https://www.ibiden.com/ir/library/statement/items/tannshinn2026Q2.pdf)
- 2026-11-02 [Company Q2 Q&A](https://www.ibiden.com/ir/items/en_QA_FY2026Q2.pdf)

### Unimicron
- 2026-10-27 [MOPS company announcement reproduced](https://financialfilings.com/filings/unimicron-3037/earnings-release/2026/74787084/)
- 2026-11-06 accessed [official monthly sales](https://www.unimicron.com/money01.html)

### ディスコ
- 2026-10-22 [H1 financial results and 9M guidance](https://www.disco.co.jp/jp/ir/library/doc/fr/fr20261022.pdf)

### Teradyne
- 2026-10-27 [Q3 company results, call October 28](https://investors.teradyne.com/news-events/press-releases/detail/455/teradyne-reports-third-quarter-2026-results)

### ASML
- 2026-10-14 [Company Q3 results](https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026)
- 2026-10-14 [SEC US-GAAP statements](https://www.sec.gov/Archives/edgar/data/937966/000162828026065813/financial_statementsxusx.htm)

### アドバンテスト
- 2026-10-28 [Q2 company financial release](https://www.advantest.com/document/en/investors/ir-library/result/E_FR_FY2026_2Q.pdf)
- 2026-10-28 [Financial review: financial income mainly investment gains](https://www.advantest.com/en/investors/financial-highlights/review/)
