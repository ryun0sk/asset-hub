# 無料のMacローカル版MBO調査の技術設計

設計日：2026-10-18（日本時間）。既存Asset HubのPython backend・素のHTML/CSS/JavaScriptを使い、SQLiteとMac内のファイルだけでMBO候補の根拠と企業価値を確認する技術設計。同日にCSV持込を中心とした初版を実装した。[起動方法・CSV仕様・実装範囲](../../../../docs/mbo-weekly.md)が利用時の正本。本書にある詳細な正規化テーブル、EDINET収集、XBRL自動抽出などは後続案として残す。初版DBはappend-onlyレコードと取込台帳・run台帳にまとめ、原本と結果は別ファイルに保存する。株式評価・候補抽出ルールの全体は[無料版の設計プラン](report.md)を参照。

「無料」は追加の有料API・有料データ契約・外部LLM・クラウド資源を必要としない構成を指す。基礎版は資料とCSVの持込だけで完結し、支払手段の登録も不要。既存Mac、通信、電気、手動調査の時間は必要。Cloud Run等の無料枠や試用クレジットを費用成立の条件にしない。EDINETの自動取得は追加の任意経路で、既定は無効。APIの無償提供を現行の公式資料で明示確認できていないため、無料APIと断言せず、料金・登録条件を確認してキーを準備した後に有効化する。

## 1. 既存コードを読んだ結論

| 確認したファイル | 現状 | 無料ローカル版への影響 |
|---|---|---|
| [backend/server.py](../../../../backend/server.py) | `K_SERVICE`でCloudを判定。通常のローカル実行は127.0.0.1待受、Hostもlocalhost/127.0.0.1に限定。GET/HEADのみ。起動時にassets/costsの文書を設定する | MBO専用モードではCloud判定による起動へ進めず、MBO以外の文書を初期化しない |
| [backend/storage.py](../../../../backend/storage.py) | LocalDocumentとGCSDocumentが同居。GCSDocumentは生成時にGoogle認証を利用し得る | MBOはSQLite専用repositoryとし、GCSDocumentを生成しない |
| [web/app.js](../../../../web/app.js) | 最後に`initCostAlerts()`と`initAssets()`を無条件実行 | 単にMBOタブを足すと、MBOだけ見ても無関係なAPI取得が始まる。MVPは専用entryを使う |
| [web/workspace.js](../../../../web/workspace.js) / [web/catalog.js](../../../../web/catalog.js) | ホーム・ナビ・調査ライブラリと`#ai`等のhash routeを構築 | MBO画面は既存の日付別調査routeとは分離。全体ホームからの導線は後段でcapabilityに応じて追加できる |
| [backend/paths.py](../../../../backend/paths.py) | research配下の許可された拡張子を静的配信し、配信可能な研究資料をデプロイ時の同梱対象にする | 私的原本・DB・評価出力をresearchへ置かない。`.gitignore`だけではHTTP配信や同梱の防止にならない |
| [scripts/build_catalog.py](../../../../scripts/build_catalog.py) | 定義済みの文書名とsources配下PDFを研究カタログ化 | 研究設計書だけをカタログへ登録する。MBOの私的データをこのスクリプトに走査させない |
| [infra/deploy.py](../../../../infra/deploy.py) | 許可されたweb・researchファイルとbackend直下のPythonファイルをステージし、Cloud Build/Runやコスト用資源を設定する。backendの新しいサブpackageは現在のglobに入らない | 無料版の起動・更新経路には入れない。MBO packageはmbo-local分岐内だけで遅延importし、通常/Cloud起動を新packageの同梱に依存させない。`--skip-costs`も無料ローカルモードの代わりにはならない |
| [.gitignore](../../../../.gitignore) | `data/private/`、`.env`、`.env.*`を除外 | DB・原本・個別評価を`data/private/mbo/`へ保存する基盤は既にある。秘密の保存先にする意味ではない |

通常ローカル版の`/api/costs`は保存済みの費用文書を読む処理であり、そのGET自体がBigQueryクエリを発行するわけではない。本案が切り離す目的は、MBOの起動に無関係な機能・個人資産・Cloud設定を必要とさせず、将来の変更でも有料経路へ入れないことにある。

## 2. モードと画面の境界

### 2.1 推奨する最小構成

同じ`backend.server`に明示的な`--mode mbo-local`を追加し、MBO専用entryを返す。通常のAsset Hubの挙動は既存モードに残す。初期実装で`web/app.js`全体の初期化方式を変更する必要を避ける。

```text
Mac内の入力ファイル                      EDINET（明示的な収集時だけ）
  CSV・PDF・XBRL・案件台帳                       │ APIキーは収集CLIのみ
             └────────────┬─────────────────────┘
                          ▼
       python3 -m backend.mbo …（唯一の書込側）
       import → normalize → validate → screen/value → publish
                          │
              data/private/mbo/
              state.sqlite + raw/ + runs/ + published/
                          │ 読取専用
                          ▼
       python3 -m backend.server --mode mbo-local --port 4331
       127.0.0.1のみ / 外向き通信なし / GET・HEADのみ
                          │
                          ▼
       web/mbo.html + mbo-app.js + mbo.css + 既存tokens.css
       根拠一覧 → 企業詳細 → 価格・シナリオ → 欠測・実行履歴
```

起動仕様の例：

```sh
# 将来実装する起動方法。APIキー・GCP認証・既存資産データは不要。
python3 -m backend.server --mode mbo-local --port 4331
# ブラウザで http://127.0.0.1:4331/ を開く。
```

| モード | rootのentry | APIと配信対象 | 外部接続 |
|---|---|---|---|
| 既存モード | 既存index.html / app.js | 現行assets・costs・catalog・research | 既存仕様を維持 |
| 新設mbo-local | 新設mbo.html / mbo-app.js | 下記MBO用GET/HEADと、指定した画面assetだけ | serverは常に禁止。CLIのEDINET収集は条件確認後に別途有効化 |

mbo-localは次の順で確定する。

1. 起動引数を読み、`K_SERVICE`が存在する環境でmbo-localを指定した場合は起動エラーにする。Cloud上でローカル限定の認証境界を流用させない。
2. mbo-localを先に分岐し、`assets`・`costs`・`cloud`の初期化、Google認証、GCS/BigQuery clientの生成を行わない。`ASSET_STATE_BUCKET`等がMacの環境に残っていても参照しない。
3. サーバーはIPv4の`127.0.0.1`だけにbindする。LAN公開用の`--host`オプションは設けない。ポート競合は停止し、別のアドレスへフォールバックしない。
4. mbo-localでは`/api/assets`、`/api/costs`、`/api/catalog`、`/research/*`、その他のweb assetを404にする。通常/Cloudモードでは`/api/mbo/*`とMBO専用entry/assetを404にする。メニューを隠すだけで分離しない。
5. `/`と`/mbo.html`は同じMBO専用entryへ割り当てる。専用entryは`app.js`、`assets.js`、`costs.js`をimportしない。フォント・ライブラリ・画像は同梱分だけを使う。

MBO内のroute例は`#mbo/candidates`、`#mbo/company/<security_id>`、`#mbo/runs`。通常Asset Hubの`#r/<研究ID>/…`と混ぜない。MBO候補の有無と調査カタログの取得成功を結び付けない。

### 2.2 全体ホームからの導線

MVPでは別ポートのMBO専用入口をブックマークして使える。既存ホームへ統合する段階では`GET /api/capabilities`等の明示的な機能情報と、`workspace.js`の表示条件を加える。CloudでMBOへの導線を出さず、APIも有効にしない。既存Cloud画面から利用者のlocalhostへ自動接続する実装や、MacのデータをCloudへ転送する実装は採らない。

通常Asset Hubからの起動導線を後日加えても、MBO専用entryを使用する境界を保つ。mbo-local自身は汎用capabilitiesの取得を必要とせず、後述`/api/mbo/status`で稼働範囲を返す。

## 3. 保存配置とデータ契約

```text
backend/mbo/                         # 将来作るPythonパッケージ
  __main__.py                        # CLI。import/collect/build/publish/status/backup
  config.py                          # 固定provider、ローカルパス、制限値
  db.py / migrations/                # SQLite schema・migration・読取用repository
  imports.py / edinet.py              # ファイル取込 / 明示的なEDINET取得
  normalize.py / validate.py          # 定義・単位・時点・証拠の確認
  screen.py / valuation.py            # 決定的なルール・計算。外部LLMなし
  export.py                          # 私的な閲覧用JSONを原子的に発行
data/private/mbo/                     # 全体がGit対象外。通常静的配信対象外
  state.sqlite                       # 正規化値・検証履歴・入力関係
  raw/<sha256>/original.<許可拡張子>   # 変更しない原本。秘密は保存しない
  imports/<import_id>/manifest.json   # sanitized出所・CSV列対応・取込結果
  runs/<run_id>/                      # 入力ID、ルール版、検証結果、計算結果
  published/<run_id>/                 # ブラウザAPIへ渡せるDTOのみ
  published/current.json              # 最後に成功したrun_idだけを指す
  backups/<backup_id>/                # Mac内の明示的なバックアップ
```

設計書等を除き、原本、会社別調査メモ、SQLite、処理ログ、出力JSONを`research/`・`web/`へコピーしない。環境変数のダンプも保存しない。画面は`published`を直接静的配信せず、MBO APIが項目を選んで返す。

DBが存在しない場合、GETサーバーはDBやフォルダを自動作成しない。状態を`empty`として200応答し、資料/株価の取込手順を表示する。初期化とmigrationは書込CLIが行う。読み手は`sqlite3`の読取専用接続を使用する。

### 3.1 SQLiteの最小スキーマ

IDは文字列、金額・倍率の計算はDecimalを用い、保存は精度を失わない10進文字列とする。証券コードは文字列とし、英字入りを許容する。SQLはplaceholderで値を渡し、sort列・指標名・statusは固定列挙から選択する。

| テーブル | 主要列 | 制約・扱い |
|---|---|---|
| `schema_version` | version、applied_at | CLIだけが更新。新しすぎるschemaは表示側で503とし、勝手にdowngradeしない |
| `issuer` / `security` | issuer_id、security_id、name、edinet_code、exchange、security_type | 法人と株式を分離。4桁コードを永久IDにしない |
| `identifier_history` | security_id、kind、value、valid_from、valid_to、evidence_id | コード変更・上場廃止・社名変更を保存 |
| `universe_snapshot` / `universe_member` | universe_id、as_of、source_id、security_id、inclusion、reason | 「全市場」と「持込銘柄集合」を区別。未取得を対象外と混同しない |
| `source_document` | document_id、provider、provider_id、source_url、published_at、observed_at、sha256、raw_relpath、mime、supersedes_id、withdrawn_at | URLは秘密を除去したもの。相対パスはDB内部だけ。原本を上書きしない |
| `import_batch` | import_id、kind、input_hash、mapping_version、started_at、finished_at、status、accepted_count、rejected_count | 同じ内容・同じmappingの再取込は重複させない。問題行を件数と理由で返す |
| `fact` | fact_id、security_id、metric、value_decimal、unit、currency、period_start/end、consolidation、fact_kind、share_basis_id、document_id、locator、public_at、ready_at、quality_status、missing_reason | 実績/会社予想/外部予想/独自仮定を分ける。欠測valueはNULL |
| `price_observation` | price_id、security_id、price_decimal、currency、price_at、time_precision、exchange、price_type、adjustment、share_basis_id、source_document_id、observed_at、quality_status | 株価は財務factと分離。取込日を価格基準日にしない。close・参考値等も区別 |
| `share_basis` / `corporate_action` | basis_id、effective_at、split_ratio、shares、treasury_shares、evidence_id | 株価・株数・1株指標の基準がそろわなければ計算保留 |
| `ownership` / `ownership_relation` | observation_id、issuer_id、holder_name、ratio、as_of、public_at、relation_type、evidence_id、review_status | 名義と実質所有者を分離。創業家等の関係は根拠付きで確認 |
| `event` / `event_observation` | event_id、security_id、event_type、status、first_report_at、announced_at、settled_at、offer_price、evidence_id | MBO公表済み・検討報道・成立・撤回・他TOBを別状態にし、探索候補と分ける |
| `review` | review_id、target_type/id、action、old_value、new_value、reason、evidence_id、reviewed_at | 人手確認・補正はappend。原本・初回抽出値を消さない |
| `run` | run_id、as_of、universe_id、input_manifest_hash、rule_version、valuation_version、started_at、finished_at、status、network_mode、provider_requests | `api_cost_jpy=0`は費用未計測の意味にしない。外部有料provider呼出数が0である記録を別に残す |
| `feature_result` / `valuation_result` | run_id、security_id、input_ids、value、status、reasons、scenario_id、assumptions、price_id | 事実から作る抽出順と価格比較を分離。NULLは0に変換しない |

数値の状態は`verified / pending / conflicting / missing / not_applicable`。理由は`not_disclosed / not_imported / parse_failed / definition_mismatch / stale / missing_price / missing_basis`等。財務値・価格・所有関係ごとに品質を持ち、一つの総合的な「データ正常」で未確認を隠さない。

`public_at`、`observed_at`、`ready_at`は別に保持する。日付だけ分かる場合は時刻精度も保存する。過去検証用に後日取得した資料へ過去の`observed_at`を作らない。現在のファイルで当時版を確認できない指標は過去検証から外し、事後再構成と前向き評価を分ける。

### 3.2 キーなしの持込CSV

最低限、次の入力を受けられる。形式の検証・previewを行ってから一括commitし、必須列不備や定義の衝突があればbatch全体を拒否する。問題行を黙って除いた成功表示はしない。

利用者は証券コードと資料上の数値を入力し、内部IDを手作業で発行しない。取込時にコード・取引所・基準日から既存証券へ対応付け、未登録なら企業・証券IDを生成する。候補が複数ある場合は対応を確定するまで保留する。

| 入力 | 必須項目例 | 任意項目・注意 |
|---|---|---|
| `securities.csv` | code、name、exchange、security_type、as_of、source | 対象集合の出所を保存。手動10社なら「登録10社」と表示。security_idは取込時に発行 |
| `facts.csv` | 解決可能なcodeまたはsecurity_id、metric、value、unit、period_end、fact_kind、source、locator | 会計期間・連結範囲・通貨・基準が必要な指標ではそれらも必須。参照原本がなければpending |
| `prices.csv` | 解決可能なcodeまたはsecurity_id、price、currency、price_date、price_type、adjustment、source | 価格は正の有限値。市場・銘柄が曖昧なら対応を保留。share_basis_idは確認済み株数・分割履歴からシステムが対応付け、不明ならmissing_basis。株価CSV自体がなくても起動できる |
| `events.csv` | 解決可能なcodeまたはsecurity_id、event_type、status、announced_atまたは不明理由、source | 既発表案件を未発見候補から除外するために使う。取引種別は人が確認 |

UTF-8を標準とし、明示指定でUTF-8 BOM/CP932に対応する案。日付はISO形式、桁区切り・括弧負数・空文字はmapping規約で扱う。`NaN`・無限大・通貨混在を拒否する。CSVセルの数式は実行しない。書き出して表計算ソフトで開く場合は、数式として解釈される先頭文字を無害化した表示用列と、内部の正規化値を分ける。

## 4. API契約と価格未入力時の表示

### 4.1 共通契約

- GET/HEADのみ。HTTPから取得開始、ファイルアップロード、任意パス読込、DB編集、外部URL fetchを提供しない。
- `schema_version=1`、`run_id`、`as_of`を返す。各ページは最初に選んだ`run_id`を後続リクエストへ渡し、一覧と企業詳細で異なるrunを混ぜない。
- `latest`の解決後は具体的なrun_idを用いる。該当runがない場合は404。最後の正常runがあるのに最新buildが失敗した場合は、正常runと更新失敗状態を並べて返す。
- `application/json; charset=utf-8`、`Cache-Control: no-store`、`nosniff`、既存API用CSPを使う。ブラウザlocalStorage・Service Worker・外部分析SDKへ私的データを保存しない。
- APIに原本のbytes、rawパス、Macの絶対パス、キー、完全な環境変数、接続先の認証クエリを含めない。根拠は短い確認用引用、書類名、ページ/項目、sanitizedした公式URL、確認状態に限る。
- `limit`は既定50・最大200、`offset`は非負整数。検索長、返却サイズ、絞込列を制限する。未知のsortや不正なrun_idは400。
- エラーは`{error:{code,message,retryable}, request_id}`。詳細stack trace・SQL・レスポンス中の秘密は画面へ返さない。データ0件はエラーにしない。

| API | 主な入力 | 応答の要点 |
|---|---|---|
| `GET /api/mbo/status` | なし | mode、offline、storage_state、schema_version、latest_success_run_id、last_attempt、edinet設定状態、許可機能。キーはconfigured/missingのみ |
| `GET /api/mbo/runs` | limit、offset | 成功・失敗runと対象集合・rule版。秘密を含まない失敗理由 |
| `GET /api/mbo/candidates` | run_id、q、status、sort、limit、offset | 候補根拠、確認状況、欠測、価格日、価値評価の状態。`coverage`に対象集合・価格あり件数等 |
| `GET /api/mbo/companies/<security_id>` | run_id | facts、ownership、event、evidence、価格、シナリオ、欠測、入力関係。短い引用を含む |
| `GET /api/mbo/events` | run_id、status、limit、offset | 公表済み/報道/成立/撤回等の監視一覧。候補と混在させない |

空状態の`status`例：

```json
{
  "schema_version": 1,
  "mode": "mbo-local",
  "offline": true,
  "storage_state": "empty",
  "latest_success_run_id": null,
  "edinet": {"configured": false, "collection_enabled": false},
  "features": {"file_import_cli": true, "http_write": false, "llm": false, "cloud": false}
}
```

キーなしではMBO画面全体をエラーにしない。「ローカル資料から調査できます。EDINETの自動取得は未設定」と表示する。server側でキーを読む必要もないため、`configured`はCLIが残した秘密を含まない最終設定確認の状態とし、不明なら`unknown`を返す。サーバー起動時に認証試験をしない。

### 4.2 価格と価値を混同しない応答

```json
{
  "security_id": "sec-example-001",
  "candidate_review": {"status": "pending", "evidence_rank": 7},
  "price": {"value": null, "currency": "JPY", "price_at": null, "status": "missing", "reason": "not_imported"},
  "valuation": {
    "standalone": {"status": "ready", "scenario_basis": "own_scenario"},
    "discount_to_base": {"value": null, "status": "pending", "reason": "missing_price"},
    "lbo_feasibility": {"status": "pending", "reason": "missing_debt_terms"}
  },
  "mbo_probability_12m": null
}
```

これは形の例であり実在企業の評価結果ではない。`evidence_rank`は定義したルールによる調査優先順であり、MBOの発生確率を示さない。単独継続価値は必要な財務・仮定がそろえば価格なしでも算出できるが、割安率は価格入力後だけ算出する。LBOのデータ不足も価格欠測と別の理由にする。

| 状態 | 画面表示 | 並べ替え・集計 |
|---|---|---|
| 株価未入力 | 「株価未入力」「割安率は未計算」。価値があれば独自シナリオとして表示 | 0円・割安率100%にしない。価格を使う並べ替えでは有効値の後ろに置き、未入力件数を示す |
| 価格はあるが株式分割基準が不一致 | 価格と基準日を表示し、「分割基準の確認待ち」 | 割安率・PER・時価総額など基準依存計算を保留 |
| 株価が古い | 「YYYY-MM-DD終値」「価格更新が必要」 | 当日の価格に見せない。古さの許容日数はrule設定で表示し、最新評価の順位から分離 |
| 1株価値の前提不足/矛盾 | 「価値評価を保留」および不足項目 | 0円へ変換せず、割安順の比較対象から外す |
| 株数が0以下・非有限値、基準1株価値が0以下 | 株数不正は計算保留。残余価値0以下は「このシナリオでは株主残余価値なし」。負の株価を表示しない | 割安率はnull、理由はinvalid_share_countまたはnonpositive_equity_value。負値を分母にする100%超の割安率を防ぐ |
| MBO公表済み | 「公表済み案件」と発表日・買付価格 | 未発見候補から除外。買付価格を公表前の予測入力に使わない |
| MBO確率未検証 | 「確率は未検証」 | 0%や確率風の点数を表示しない |

画面上部には「対象：持込N社/確認済みN社」「財務の対象期」「資料の最終確認日」「株価の基準日」「計算run」を表示する。企業ごとに日付が違う場合は「基準日が異なる」と件数を出し、単一の更新日時で全件の鮮度を代表させない。数値なし・0件・API障害・処理中は別表示にする。

## 5. 取得・認証・原本の安全な扱い

### 5.1 ネットワークと認証

既定は`offline`かつEDINET収集無効。資料・CSVの取込、候補抽出、数値計算、閲覧はネットワーク接続なしで完結させる。EDINET取得は現行の料金・登録条件を確認して任意で有効化した場合だけ、独立した明示CLIから使う。キーが存在するだけではネットワーク取得を許可しない。

```text
python3 -m backend.mbo import --kind <種類> --file <Mac内ファイル>
python3 -m backend.mbo build --as-of <基準日> --universe <対象集合ID>
python3 -m backend.mbo publish --run-id <検証成功run>
python3 -m backend.mbo collect edinet --from <日付> --to <日付>
```

いずれも将来のCLI仕様例。import/build/publishにはキーを要求しない。`collect edinet`だけが`EDINET_API_KEY`等のローカル環境変数、またはユーザーが許可した既存の秘密管理からプロセス内で受け取る。コマンド引数、repo内config、DB、取込manifest、画面JSONへ秘密を書かない。`.env`がGit対象外であることを理由にキー保存を促さない。

サイトログインや認証補助が必要になった場合は共通site-login skillの制約に従う。実体の参照先は`/Users/ryu/.codex/skills/site-login/SKILL.md`。ユーザーが選別したAI Logins専用Vault・共通brokerだけを利用し、個人Vaultや通常の`op`操作へ切り替えない。OTPは本人へ引き継ぐ。本案を保存するだけではVault参照・ログイン・キー取得を行わない。

EDINET clientは公式hostと必要なpathに固定し、任意URLを受けない。APIキーがqueryに入る場合を含め、ログはURL全体を保存せず、provider・書類ID・HTTP状態・件数・時刻だけを記録する。リダイレクト先へキーを転送しない。認証失敗は再取得ループをせず停止し、以前の成功データの閲覧を続ける。取得上限、timeout、429/5xxの上限付き再試行、取得済みhashの再利用を行う。

J-Quants、バフェット・コード、従来TDnet API、外部LLM、X API、GCPのclient/SDKをMBO実行経路へ組み込まない。既存X API利用の300円枠は再利用しない。会社IRはまず本人が取得したファイルの持込を受け、汎用URL downloaderや全市場crawlerは初期実装に含めない。

### 5.2 ファイルと表示

- 新規privateディレクトリは0700、ファイルは0600を基本に作る。既存の他領域の権限を一括変更しない。SQLiteのWAL/SHM、一時ファイル、backupも同じprivate領域に置く。
- importは通常ファイルだけを読み、symlinkやprivate root外へ逸脱する出力を拒否する。名前はhash/内部IDへ置き換え、入力の相対パスをそのまま出力パスに使わない。
- ZIPは展開前のサイズ・ファイル数・圧縮比、展開後の総量を制限し、`..`、絶対パス、Windows形式の逸脱、symlinkを拒否する。XMLは外部参照/DTDを拒否し、要素数・深さ・サイズ制限を設ける。HTML/JavaScriptを実行しない。
- PDF・画像は原本保管まで受け付けても、抽出器がない/テキストを抽出できない場合は`parse_failed`とし、CSVや人手確認で補う。外部OCR/LLMへ自動送信しない。XBRL拡張tagや会計定義の不明項目を似たラベルだけで確定しない。
- MBO画面に取得HTMLをiframeで挿入せず、原文や会社名・CSVセルは`textContent`等で表示する。リンクは許可されたHTTPS出所だけを扱い、`javascript:`、`file:`等を拒否する。
- 原本を`/api/mbo/raw/...`で取得するrouteは設けない。根拠の全文確認はsanitizedした公式URL、またはMac内で原本を手動で開く。APIから任意のローカルアプリを起動しない。

オフライン時は画面の書類IDを使い、将来実装する読取専用CLI `python3 -m backend.mbo evidence locate --document-id <書類ID>` で保存済み原本の所在を確認する。保存ハッシュとの一致を検査してMac内のパスを端末に表示し、利用者が原本を開く。絶対パスはAPI・ブラウザ・実行ログには含めず、CLIから自動でアプリやリンクを起動しない。

### 5.3 HTTP境界

既存のHost検査を維持し、`127.0.0.1:<実ポート>`/`localhost:<実ポート>`以外、重複/不正なHost、cross-siteな`Sec-Fetch-Site`、不一致のOriginを拒否する。CORSを有効にしない。キーやAPI認証をブラウザへ渡さない。APIの副作用をなくし、外部ページからの取得開始や書込を成立させない。

専用画面のCSPはselfだけを基本にし、`object-src 'none'`、`frame-ancestors 'none'`等を維持する。rawのHTMLやCDN scriptを許可する既存研究用CSPをMBO画面へ転用しない。localhost限定はこのMacの他プロセスを認証する仕組みではないため、本人のMac・本人のOSアカウントで使う範囲を前提にする。

## 6. 実行・公開・復旧

書込CLIは単一実行lockを取得し、SQLite transactionと`foreign_keys`を使う。WALを採用し、サーバーの短い読取とCLI書込を分離する。schema migration、正規化値・証拠・reviewのcommitは原子的に行い、長いファイルdownload中にDB transactionを保持しない。

buildは既存runを書き換えず、新しいrun_idで入力ID・hash・抽出版・計算版・基準日時を固定する。publishは検証成功runだけを対象とし、DTO群を同じprivate領域の一時ディレクトリに完成させてからrenameする。最後に`current.json`をatomic replaceする。失敗時に前回成功版を「最新」と取り違えないよう、`last_attempt`と`latest_success`を別々に表示する。

各APIは選択runに固定されたpublished DTOを返す。人手補正が加わっても表示済みrunは不変で、新しいbuild/publish後に初めて更新する。既存runを選んだブラウザが、裏で別runへ自動的に移ることはない。更新ボタンで新しい成功runへ切り替える。

バックアップはSQLiteのbackup API等で整合したDBコピーを作り、そのDBが参照するraw・run manifest・publishedをhash一覧付きでMac内に保存する。稼働中のWAL方式DBを単一ファイルだけ単純コピーしない。復元は別の一時ディレクトリで整合性と参照原本のhashを確認し、server/CLI停止後に差し替える。秘密はbackupに含めない。

初期は手動実行。Macがsleep/電源OFFの間は取得・再計算されない。「最新情報を監視中」と表示しない。定期実行が必要になった場合も、別の明示指示でローカル実行を設定し、この設計書からCloud Scheduler・有料通知・定期API呼出しを開始しない。

## 7. 実装時の変更対象

本書作成では以下を変更しない。将来、既存のユーザー差分を確認したうえで実装する候補である。

| 対象 | 変更内容 | 初期実装の要否 |
|---|---|---|
| `backend/server.py` | `--mode mbo-local`、モード先行分岐、専用entry/asset/API、非MBO機能の初期化回避、statusコード | 必須。既存Cloud/IAPのテストを維持 |
| 新規`backend/mbo/*` | CLI、SQLite、取込、EDINET固定client、定義/品質確認、screen/value、DTO publish | 必須。データ持込とoffline buildを先に作る |
| 新規`web/mbo.html` / `web/mbo-app.js` / `web/mbo.css` | 専用画面、候補/企業/案件/履歴、空/欠測/障害状態、同梱assetだけ使用 | 必須。`tokens.css`等既存の見た目を再利用 |
| `backend/paths.py` | MBO専用assetの明示allowlistを追加するか、MBO module内に専用resolverを置く | 配信境界を試験する。汎用private resolverは追加しない |
| `web/workspace.js` / `web/app.js` / `web/index.html` / `web/catalog.js` | 通常UIからの任意のMBO入口。capabilityに応じた表示/route | MVPでは不要。専用entryで動作した後に検討 |
| `scripts/build_catalog.py` | 設計書をカタログへ直接載せる場合の文書名登録 | privateを走査する変更は不要。MBO画面は研究カタログに依存させない |
| `README.md` / テーマ`README.md` / 将来`docs/mbo-local.md` | 起動、CSV仕様、手動運用、private境界、今回の設計への相対リンク | 必須。設計書と私的データを区別 |
| `tests/test_mbo_*.py` / `tests/test_mbo_*.cjs` / `tests/test_server.py` | 下記の境界・欠測・時点・再現性の確認 | 必須。無料専用経路を守る試験を優先 |
| `.gitignore` / `infra/*` / Cloud設定 | 現在の`data/private/`除外を利用 | 無料版のための変更・実行は不要 |

catalogへ登録する公開設計書には会社原本やprivateデータへのリンクを入れない。同日の当初案はinitial-paid-plan.mdとtechnical-design.mdに残し、現行の主プランをreport.mdに置く。READMEの導線とカタログはこの主プランを指す。既にアーカイブ化された過去日付のファイルを変更しない。

## 8. 受入確認

実装時に合否を確認する条件。以下の試験は今回実行した結果ではない。

| 試験 | 合格条件 |
|---|---|
| キー・GCP設定のない初回起動 | Pythonと同梱ファイルだけでmbo-localが起動し、status/空画面を表示。DBなし・価格なし・EDINETキーなしを正常な未設定状態として扱う |
| 完全offlineの持込経路 | 外向きネットワークを無効化した環境で、テスト用銘柄・財務・価格CSVのimport → build → publish → ブラウザ表示が完了。価格CSVなしでも根拠一覧と不足項目を表示。必須有料サービス0、支払手段登録なし |
| 有料/Cloud経路の遮断 | Google認証、GCSDocument生成、GCS/BigQuery、外部LLM、J-Quants、バフェット・コード、X APIを「呼ばれたら失敗するstub」にしてMBO操作が通る。無関係なCloud環境変数があっても呼ばない |
| UIの通信 | 初期表示・候補検索・企業詳細・run切替で同一originの許可assetと`/api/mbo/*`だけを取得。cost/assets/catalogのfetch、CDN、外部分析、背景pollingがない |
| Cloud分離 | `K_SERVICE`ありのmbo-localは起動前に失敗。既存Cloud/通常モードのMBO APIは404。通常/IAP境界を変えない |
| bind/Host/Origin | socketが127.0.0.1のみで待受。不正Host・cross-site取得を拒否。GET/HEAD以外は405で、副作用がない |
| 原本の非配信 | `/data/private/…`、`/api/mbo/raw/…`、`/research/../data/private/…`、符号化traversal、symlink経由を拒否。APIにrawパスや秘密を含めない |
| キーの非漏洩 | ダミーのAPIキーを与えた成功/認証失敗/timeout/redirectを試し、DB・ログ・manifest・API・画面・例外出力の全てに値がない。実キーを使って確認しない |
| 持込検証 | 文字列コード、通貨、価格日、分割基準を保持。負価格、NaN、重複衝突、必須列欠如を理由付きで拒否。XML/ZIPの逸脱と過大入力を拒否 |
| 価格未入力・基準不一致 | 未入力を0円/100%割安と表示しない。価値と価格比較のstatusが独立。分割基準不一致・古い価格・未確認数値で順位を誤らせない。株数0以下・非有限値を拒否し、基準1株価値0以下では割安率をnullにする |
| 証拠・時点 | 主要表示値からdocument/locator/reviewへ遡れる。オフラインでも書類IDから原本所在とhashを確認できる。訂正版と元版を保持。未来資料や発表後の計画を混入させたfixtureを保留/除外できる |
| 冪等性・計算再現 | 同一hashの再取込で行が増えず、同じ入力manifestと計算版で同じ数値出力。run間は勝手に混ざらない |
| build失敗と復旧 | import/publish途中の強制失敗で前回成功runを閲覧可能。新旧DTOが混在しない。backupからDB・raw参照の整合性を復元できる |
| 既存画面の回帰 | 既存API、研究カタログ、日付別route、IAP検証、304/HEAD等が既存モードで維持される。既存private資産値をMBOテストへ取り込まない |

## 9. 実装順序と残る限界

1. **持込だけのoffline版**：SQLite、CSV契約、確認履歴、専用server/画面、価格未入力表示、決定的な計算を実装する。10〜20社の小さなfixtureで動線と境界を確定する。
2. **EDINETの任意取得**：公式の料金・登録条件を確認し、希望する場合だけ有効化する。環境変数/許可された秘密管理、固定client、差分取得、XBRL/CSVの定義照合を追加する。取得できない資料や拡張tagを人手確認へ回す。この工程が未実施でも基礎版は完了とする。
3. **候補と評価の運用**：公表済み案件の除外、根拠確認、欠測率・価格鮮度・処理時間を記録し、対象集合を徐々に広げる。
4. **過去検証・定期化**：当時母集団・訂正前資料・株価基準がそろう範囲だけ検証する。必要性が確認された後にローカル定期実行や通常ホームへの導線を加える。

無料版は、持込銘柄や取得済み資料の範囲に限定された調査道具から始める。全市場の当日価格、会社予想/開示の即時網羅、上場廃止を含む完全な履歴、原本だけからの完全自動解釈は保証しない。対象集合と欠測の件数を常時表示し、入力が薄い状態で確率や全市場ランキングを作らない。

保存量や処理待ちが増えたときは、まず取得・解析の差分化、SQLite index、原本保管方針、対象集合を見直す。性能上の理由だけで有料API・クラウド・外部LLMへ自動移行しない。ソフトウェア・APIの現行仕様と利用条件の確認は、実装に採用する具体的な経路ごとに行う。

## 参照と確認範囲

- 本書の既存実装に関する記述は、2026-10-18時点の作業ツリー内のファイルを読んだ結果。既存の未commit変更があるため、実装時には最新差分を再確認する。
- EDINETの取得制約と認証の一次資料は[無料版の取得条件と出典](free-data-sources.md)を参照。本書ではAPI認証、資料収集、外部サービス呼出し、依存packageの追加を行っていない。
- 当初の有料経路を含む[技術設計](technical-design.md)は履歴として残す。無料運用の実装境界については本書のmbo-local仕様を優先する。
- 設計の整理にはengineering:system-design skillの要件・境界・データフロー・API・障害対応・trade-offの枠組みを用いた。
