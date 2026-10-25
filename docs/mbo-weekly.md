# MBO調査をこのMacで週次更新する

実装日：2026-10-18。毎週このチャットから「MBO調査を更新して」と依頼して実行する。常時稼働や自動スケジュールは不要。調査・計算はこのMacのPython標準ライブラリで動き、有料データ契約・APIキー・外部LLMを必要としない。同日の追加依頼で、普段の非公開Asset Hubにも「MBO調査」タブを組み込んだ。クラウドは保存結果の閲覧に使い、原本・DB・計算はMacに残す。

## 起動する

リポジトリのルートで実行する。

```sh
python3 -m backend.server --port 4330
```

[このMacのMBOタブ](http://127.0.0.1:4330/#mbo/candidates)で候補、企業詳細、DCF三シナリオ、LBO試算、公表案件、週次差分・履歴を確認できる。Asset Hubの「MBO調査」から「候補」「公表案件」「週次履歴」を選ぶ。2026-10-18の初回実企業調査を登録済み。画面を開いても資料の取得・株価更新・DBへの書込は起きない。停止は起動したターミナルでCtrl+C。従来の単体画面は`--mode mbo-local --port 4331`でも起動できる。

実データは`data/private/mbo/`、架空デモは`data/private/mbo-demo/`に保存する。デモと実データは混ぜられない。どちらもGit対象外。クラウドへは検証済みの閲覧用JSONだけを別途反映し、原本・DB・取込台帳は同梱・配信しない。

架空4社で動作を確認する場合：

```sh
python3 -m backend.mbo demo
python3 -m backend.server --mbo-data-dir data/private/mbo-demo --port 4333
```

デモは同日に2回の取込・計算を実行し、価格更新、株価欠測、公表案件への移動、前回差分を再現する。実在企業のデータも、過去の観測日時を偽ったバックテストも含まない。作成済みデモは上書きしない。再生成する場合は新しい`--data-dir`を指定する。

## 毎週行う作業

1. 前回の保存結果と不足情報を見る。新しく調べる企業も対象集合へ追加する。対象は「持込銘柄」であり、日本の全上場企業を網羅した結果ではない。
2. 公開IR、EDINET、手動閲覧した適時開示などから、その週に必要な原本をMacへ保存する。取得条件は[無料データの整理](../research/themes/mbo-research-system/2026-10-18/free-data-sources.md)を確認する。TDnetのスクレイピング、課金API、X APIは使わない。
3. 原本と照合して下記CSVへ入力する。百万円から円への換算、会計期間、連結/単体、余剰現金、リース負債、株式分割基準を確認する。照合が終わるまで`pending`にする。独自シナリオを実績・会社予想と混ぜない。
4. 株価も出所・基準日・分割基準とともに入力する。株価なしでも調査候補と単独継続価値は残る。公表済み・検討報道のMBO/TOBをイベント台帳へ追加する。
5. 検証後に`weekly`を実行し、画面を「保存済み結果を再読込」する。新規・移動・株価・価値・不足情報の変化を確認し、追加調査する企業を決める。

週次入力フォルダの作成例（日付は実施日に置き換える）：

```sh
python3 -m backend.mbo templates data/private/mbo-inbox/2026-10-18
# 作成されたCSVへ入力し、同じフォルダ内に原本を保存する。
python3 -m backend.mbo weekly data/private/mbo-inbox/2026-10-18 --as-of 2026-10-18 --dry-run
python3 -m backend.mbo weekly data/private/mbo-inbox/2026-10-18 --as-of 2026-10-18
```

追加行だけの取込も可能。既存の原本は`documents.csv`を再記載せず、保存済み`source_id`で参照できる。同一内容の再取込は重複させない。必須列不備・不正値を含むバッチは全体を拒否し、CSV名と行番号を返す。`--dry-run`はDBへ保存しない。同じ年度・公表日時の確認済み数値が衝突すると、計算を保留する。訂正版には新しい`source_id`と実際の公表日時を付け、過去の原本を置き換えない。

取込成功後に計算が失敗した場合、取込データは残り、最後の成功画面も保持される。入力を修正・追記して`build`を実行できる。

```sh
python3 -m backend.mbo status
python3 -m backend.mbo runs
python3 -m backend.mbo build --as-of 2026-10-18
```

誤転記を訂正するときは、`records`で入力IDを確認する。`facts.csv`/`prices.csv`に任意列`supersedes`（置き換えるrecord ID）と`correction_reason`（訂正理由）を追加する。元の入力・原本・過去runは残り、訂正を取得・確認した時点から新しい値を使う。同じ会社・指標・基準日の訂正だけ許可し、既に訂正済みの古いIDから分岐する訂正は拒否する。連続訂正では直前の訂正IDを指定する。

```sh
python3 -m backend.mbo records --kind facts --code 1234
python3 -m backend.mbo records --kind prices --code 1234
```

## CSVの列と確認条件

UTF-8（BOM可）、または明示的な`--encoding cp932`。数値は桁区切りなし、空欄は0にしない。金額はJPYの**円単位**、株数は株単位の整数。`owner_ratio`は42%なら`0.42`。日付は`YYYY-MM-DD`、時刻まで分かる場合はタイムゾーン付きISO日時。値を入力したCSVセルをプログラムや数式として実行する処理はない。

| ファイル | 主な列 | 用途・注意 |
|---|---|---|
| `documents.csv` | `source_id,file,title,source_url,published_at` | `file`は取込フォルダ内の原本の相対パス。PDF/CSV/XML/XBRL/HTML/TXT、各32MiBまで。ZIP展開・XML/PDF解析はしない。URLはHTTPS、クエリ・fragmentは除去。原本なしの値は`verified`指定でも`pending`に下がる |
| `securities.csv` | `code,name,exchange,security_type,as_of,source_id,included` | 普通株は`common_stock`、東証は`TSE`。`included=true/false`で対象集合を追加・除外。内部IDは自動発行。コード・取引所の変更や再利用は自動統合しないため人による対応確認が必要 |
| `facts.csv` | `code,exchange,metric,value,unit,currency,period_start,period_end,fact_kind,consolidation,share_basis,public_at,source_id,locator,quality_status,missing_reason` | 金額の`unit,currency`は双方`JPY`。株数は`unit=shares`、保有比率は`ratio`。`fact_kind`は`actual/company_forecast/external_forecast/own_scenario`。営業CF入力は`actual`のみ。余剰現金と公表済み株式異動からの株数推計だけは、明示的に確認した`own_scenario`を区分を保って使用できる。`consolidation=consolidated/standalone` |
| `prices.csv` | `code,exchange,value,currency,price_at,price_type,adjustment,share_basis,public_at,source_id,locator,quality_status` | 正の有限値、JPY。`price_type=close/reference`、`adjustment=unadjusted`。確認済み株数と同じ`share_basis`が必要。14日超前の価格では割安率を保留 |
| `events.csv` | `code,exchange,event_type,status,announced_at,public_at,source_id,locator` | `event_type=mbo/parent_take_private/other_tob`、`status=reported/announced/ongoing/settled/withdrawn`。初版は撤回も含めイベント登録企業を新規探索候補から分離。未確認の噂を事実として登録しない |
| `scenarios.csv` | `code,exchange,name,as_of`と下記の仮定 | `name=bear/base/bull`。全仮定を明示。未入力・不正な前提は保留。各CSVはヘッダーだけでもよい |

`quality_status`は`verified/pending/conflicting/missing/not_applicable`。`verified`は人が確認済みと申告した状態で、自動監査済みを意味しない。原本内の位置を`locator`に書く。値が不明なら空欄、`missing_reason`に理由を書く。

財務指標の対応範囲：

| metric | 内容 |
|---|---|
| `ebit` | 営業利益。年330〜380日の通期実績 |
| `depreciation` | 減価償却費。EBITと同一期・同じ連結範囲 |
| `capex` | 設備投資の支出額を正値で入力 |
| `delta_nwc` | 運転資本増加。減少は負値 |
| `cash_and_equivalents` | 会社開示の現金同等物。現預金と混同しない。独自余剰現金の同日上限を確認 |
| `excess_cash` | 運転必要額・拘束性現金を除いた独自調整。`own_scenario`を実績と区別。同じBS日の確認済み現金同等物が必要 |
| `debt` | CFとリース処理をそろえた有利子負債。年金等の追加調整が必要なら確認を完了するまで保留 |
| `noncontrolling_interest` | 非支配持分。存在しないと確認した場合だけ0 |
| `shares_diluted` | 自己株控除後・希薄化考慮後の株数。同じ分割基準の実数。最新の株数更新を優先 |
| `owner_ratio` | 根拠を確認した経営陣・創業家の保有比率。名義株主の比率から関係を自動推測しない |
| `operating_cfo` | 営業CF。設備投資との差は探索の代理指標で、FCFFの代用にしない |

シナリオの必須列：`horizon_years,revenue_growth,tax_rate,wacc,terminal_growth,entry_debt_multiple,debt_interest,debt_amortization,exit_multiple,target_irr,fee_rate,rollover_ratio,minimum_cash`。`note`に仮定の理由を記載できる。

- `revenue_growth`は簡易モデル上、EBIT・減価償却・設備投資・運転資本増加を同じ率で伸ばす仮定。売上と利益率を個別予測するモデルではない。将来の運転資本減少は0に置いて現金回収を反復せず、設備投資は少なくとも減価償却費とする保守的仮定。実績の符号・金額は書き換えない。
- `wacc > terminal_growth`が必要。赤字に即時の税還付は見込まない。残余株主価値が0以下なら負の株価を出さず、割安率も計算しない。
- LBOは基本シナリオを使用。`entry_debt_multiple`は初期EBITDAに対する固定借入倍率、`debt_amortization`は初期元本に対する毎年の返済率。CFは留保し、途中配当・追加借入・任意返済なし。出口で残債を控除して分配する。
- `fee_rate`は株式取得対価への手数料率。`rollover_ratio`は株式取得対価から経営陣等が再出資する比率。同順位の出資額比で出口を配分。`minimum_cash`は余剰現金から再控除せず、買収時に追加積立するバッファ。金融機関の融資条件ではない。
- 非支配持分がある場合、LBOは親会社へのCF帰属を追加確認するため保留。借換費用・税務・リース・年金など企業固有の調整を自動推定しない。

## 候補の順位と時点

現行の `mbo-local-4-census-checks` は、所有構造・動機・実行可能性・障害を根拠付きの状態で分け、割安度・情報確度も独立して表示する。並び順は手動の監視対象→詳細調査→調査待ち→見送りという作業順で、MBO有力度の順位ではない。未処理企業にも毎回調査枠を割り当てる。資料不足を低評価にしない。

旧4点（確認済み経営陣・創業家持分20%以上で2点、営業CF−設備投資が正で1点、余剰現金が負債超で1点）は、過去のMBOとの比較で裏付けたものではないため主順位から外した。`priority`は保存版との互換性のため残すが、新版の画面/APIは並び替えに使わない。過去runは「旧優先度」と明記して保存当時の結果を表示する。[採否判断と過去事例](../research/themes/mbo-evaluation/2026-10-18/report.md)

### MBOの論点と作業判断の取込

`assessments.csv` は任意の追加入力。`dimension,factor_id,state,evidence_type,speaker,quote,interpretation,as_of,valid_until,public_at,source_id,locator,quality_status,reviewer`と銘柄を記載する。`quote`は原文、`interpretation`は調査者の解釈、`speaker`は会社/経営者/株主/買収者/助言者/分析者を区別する。対応する15論点は [assessment.py](../backend/mbo/assessment.py) の `FACTORS` を参照。根拠IDは `records --kind assessments --code <code>` で確認できる。

- 状態は `supported / contradicted / unknown / conflicting / not_applicable`。`supported`はその論点の該当確認で、障害の論点では障害があることを示す。一部の確認で軸全体の確認完了とはしない。
- 根拠区分は `public_fact / analyst_hypothesis / own_scenario / post_announcement`。原本確認済み・有効期限内の `public_fact` だけを事前の条件確認に使う。株主提案を会社のMBO意向へ読み替えない。
- 資金合意の該当確認には当事者と条件（`agreement_parties,agreement_terms`）および原本位置が必要。LBO試算や外部の見込みだけでは合意を確認したことにしない。
- 追加した応募下限・実施前提条件・価格異論の3論点は[全件調査とAstraレビュー](../research/themes/mbo-evaluation/2026-10-18/census-2021-2026/README.md)を参照。応募合意の存在だけを下限到達、条件の列挙だけを充足、市場株価の上振れだけを株主の異論と認定しない。原文位置、数量・条件の関係、未確認部分を`interpretation`へ残す。公表後の情報は公表案件の検証に使い、未公表候補の根拠へ移さない。
- 可視な全イベント履歴の初回報道・公表日以降の説明は事後情報に分離。同一JST日は時刻差にかかわらず保守的に事後扱い。公開・取得・処理のカットオフも維持する。
- 別出典の有効な反証を新しい評価日で消さない。同じ論点に該当・反証があれば矛盾を表示し、訂正は `supersedes,correction_reason` で追記する。

`reviews.csv` は独自の作業判断。`state`（`awaiting / research / monitor / deferred`）、`reason,watch_trigger,as_of,next_review_at,public_at,source_id,locator,quality_status,reviewer,basis_record_ids`と銘柄を記載する。監視には次に確認する変化、再確認日、依拠する根拠IDのJSON配列が必須。根拠が失効・訂正・矛盾した場合は監視を再確認待ちに戻す。数値条件による監視への自動昇格は行わない。作業判断自身の原本も独自判断と明記し保存する。公表済み案件は別枠のまま扱う。

DCFは`EBIT×(1−税率)+減価償却−設備投資−運転資本増加`をWACCで割り引き、余剰現金を加算し負債・非支配持分を控除する。割安率は`(基本シナリオ価値−保存株価)/基本シナリオ価値`。必要な値・根拠がそろうまで`null`を維持する。

公表・取得・確認の日時を別に保存する。評価日のJST当日末までに利用可能な行だけ使い、後日取得した資料で過去の成績を作らない。過去の判断は当時保存したrunを画面で選ぶ。初版の年次財務は548日超で保留。株数と所有比率はその後の確認済み更新を優先し、分割基準は価格と照合する。公表済み増減からの独自株数推計は元の実績株数と画面に併記する。cash・debt・NCIは同じBS日・連結範囲にそろえ、欠測を旧値で埋めない。通期BSで参考評価する場合は一式を通期に固定し、より新しい中間期の現預金をCFEに流用しない。

## 原本・履歴・バックアップ

原本はSHA-256の保存先へ追記し、改変を検出したら次のbuildを停止する。各runに入力レコードID・入力ハッシュ・ルール版を保存し、閲覧用JSONとcurrentポインタを原子的に発行する。既存runは上書きしない。HTTPはGET/HEADだけ。ローカルはloopback限定、クラウドは既存のIAP認証で閲覧者を制限する。MBO APIは閲覧用の保存結果を読み、資産・費用・資料の取得処理とは別に扱う。

企業詳細に表示するdocument IDから原本の場所を確認できる。絶対パスはこのCLIだけに表示する。保存先を変えた場合は先頭へ`--data-dir <保存先>`を付ける。

```sh
python3 -m backend.mbo evidence locate --document-id doc-対象のID
python3 -m backend.mbo backup data/private/mbo-backups/2026-10-18
```

バックアップはSQLite backup APIと原本・履歴のコピーを使い、ファイル別ハッシュを残す。空の保存先が必要。復旧確認は、まずコピーを別の`--data-dir`へ指定して履歴と原本ハッシュを確認する。現在のデータを上書きする自動復元は提供しない。

## 実装範囲

実装済み：CSV一括検証/取込、原本保存、確認状態、対象集合、探索順位、DCF/LBO、イベント分離、immutable run、前回差分、私的バックアップ、Asset HubのMBOタブ、閲覧用JSONの選別書出し。クラウドAPIは計算を行わず、既存の非公開stateバケットにある`mbo/results.json`だけを読む。未登録なら空画面を返し、認証・データ異常は取得失敗として表示する。

## 普段のAsset Hubへ週次結果を反映する

Macでの調査を確認してから、直近52回までの閲覧用結果を書き出す。出力は原本やSQLiteを含まない。架空データの書出しは明示の`--allow-demo`なしでは拒否する。本番に架空デモを自動反映しない。

```sh
python3 -m backend.mbo export-dashboard data/private/mbo/dashboard-results.json
```

GCP認証が有効な場合、この1ファイルを既存の非公開バケットへ反映すると、最大約60秒のキャッシュ更新後にMBOタブへ表示される。コードの再デプロイは毎週必要ない。

```sh
gcloud storage cp data/private/mbo/dashboard-results.json gs://ryun0sk-asset-hub-asset-state/mbo/results.json --project=ryun0sk-asset-hub --account=ryun0sk.takagishi@gmail.com
```

認証・アップロードはこのローカル書出しコマンドから自動実行しない。GCP認証には共通site-login手順、またはその作業に明示許可された方法を使う。既存Asset HubのCloud Run/GCS利用料は従来の課金枠に含まれ、クラウド閲覧まで厳密な0円を保証するものではない。[タブ統合の検証・反映記録](changes/2026-10-18-mbo-tab/README.md)を参照。

未実装：全市場の株価自動取得、PDF/XBRLからの数値自動抽出、EDINET自動収集、OCR、創業家の実質所有関係の推定、コード変更・全コーポレートアクションの自動処理、確率モデル・過去成績検証。資料を読みCSVへ整理するところは週次調査で行う。未取得を0や「該当なし」と扱わない。

実装入口：[core.py](../backend/mbo/core.py)、[valuation.py](../backend/mbo/valuation.py)、[HTTP境界](../backend/mbo/http.py)、[CLI](../backend/mbo/__main__.py)、[画面](../web/mbo.html)。[元の無料設計](../research/themes/mbo-research-system/2026-10-18/free-technical-design.md)のうち上記を初版として実装している。

## 2026-10-18の検証記録

MBOのPythonテスト69件と画面のJavaScriptテスト12件が成功。原本欠測、取込全体の拒否、重複、明示訂正、株数更新、UTC/JST、DCFの計算恒等式、LBOの資金使途と調達、返済不能、価格・分割基準、未来データ除外、前回結果の保持、バックアップ、HTTP読取による非変更、外部Origin拒否を確認した。ソケットを禁止してもデモの取込→計算→発行が完了する。既存機能を含むPython/JavaScriptの回帰検証も成功した（既存の環境依存テストのskipあり）。

ブラウザでは実データの空状態、架空候補、株価なしの絞込、企業詳細のDCF/LBOと根拠、公表案件、前回差分を確認。390px幅で文書全体の横はみ出しなし、ブラウザの警告・エラーなし。[検証時の架空デモ画面](../research/themes/mbo-research-system/2026-10-18/working/mbo-weekly-demo.png)はローカル補助画像として保存した。

```sh
python3 -m unittest tests.test_mbo_core tests.test_mbo_time tests.test_mbo_valuation tests.test_mbo_corrections tests.test_mbo_http -q
node tests/test_mbo_ui.cjs
python3 scripts/check_design_tokens.py
python3 scripts/archive_snapshots.py --check
```

## 初回の実企業調査

2026-10-18に23社の適格性を確認し、6社を深掘りした。19社の探索対象とMBO公表済み1社をタブへ登録し、上場廃止・再編済み3社を除外。年次BSをそろえた参考DCF比較は2社、残る深掘り4社は未確認値・事業範囲変更・実績在庫負担等により割安率を保留した。[初回の評価と条件](../research/themes/mbo-candidates/2026-10-18/report.md)を参照。
