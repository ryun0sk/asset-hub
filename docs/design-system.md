# Asset Hub デザインシステム

Asset Hub（全資産の週次推移と株式投資の調査ダッシュボード）の画面は、Pathosion Ops ダッシュボードと同じ見た目・部品の考え方で作る。ネイビーの左サイドバー、白いトップバー、`.metric` のタイル、`.panel` の表、コストタブ、共通グラフ部品をそのまま踏襲し、ロゴ画像の代わりにテキストのワードマーク「Asset Hub」を使う。文字・色・線・余白の値は `web/tokens.css` だけに置き、実行時に他リポジトリへ依存しない。ライトテーマのみ。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `web/tokens.css` | 文字サイズ・ウェイト・行間・余白・ブランド色・状態色・グラフ色・線幅・角丸。値（カスタムプロパティ）の唯一の定義場所 |
| `web/styles.css` | シェル（サイドバー・トップバー・見出し・タイル・パネル・表・バッジ）。参照ダッシュボードの寸法を移植した既存CSS |
| `web/costs.css` | コストタブ。参照ダッシュボードから移植。色はトークン化済み |
| `web/assets.css` | 資産画面（保有・推移）：ツールバー、チェックボックス行、保有表、増減表、空状態。新規CSS |
| `web/app.css` | ワードマーク、クラス別ナビ、調査一覧の表、資料ビューア（iframe・コード表示）。新規CSS |
| `web/doc.css` | Markdown表示（`.doc`）。新規CSS |
| `web/charts.js` / `web/charts.css` | 共通グラフ部品 `UiCharts` と `.ui-chart*` のスタイル。ページ側で上書きしない |
| `web/markdown.js` | 安全なMarkdownレンダラー（下記） |
| `web/catalog.js` | 調査カタログと既存日付別URLの参照、ハッシュルーティング（純粋関数） |
| `web/app.js` | 画面の切り替え、サイドバー、資料ビューア |
| `web/cost-model.js` / `cost-view.js` / `costs.js` | コストの集計・表示・取得（5分ごとの再取得とサイドバー警告） |
| `web/asset-model.js` / `asset-view.js` / `assets.js` | 資産の集計（純粋関数）・表示（HTML文字列）・取得（`/api/assets`、60秒TTL、タブ復帰時に再取得。ポーリングなし） |

読み込み順は `tokens.css` → `styles.css` → `charts.css` → `costs.css` → `assets.css` → `app.css` → `doc.css` → `ai-valuations.css` → `workspace.css`。

## 画面の構成

- **スクロール**：本文・表・コードは内容の高さで展開し、縦方向はページ全体でスクロールする。ボックス内に縦スクロールを作る `height` / `max-height` 制限は基本使わない。幅広い表・グラフ・コードの横スクロール、固定サイドバーとPDFビューアは用途に応じて残す。
- **サイドバー**：主要入口は「ホーム」「保有・推移」「AI関連銘柄・サプライチェーン」「調査ライブラリ」「コスト」の5つ。「保有・推移」の4子項目を常設し、AI閲覧中は「銘柄を比較」「事業を理解」「考察と根拠」の見出しで子項目を展開する。その他の資料を読むときはライブラリの下にその対象の資料だけを展開する。選択中は背景と青い点、`aria-current` で示す。スマホでも子項目を表示する。
- **トップバー**：「Asset Hub / 現在の画面」のパンくず。資料表示中は右側に調査日と「新しいタブで開く」。
- **ホーム**：よく使う2つの入口をカードで並べ、資産サマリー・推移・保有一覧・方針、AI銘柄比較・全体像へ直接移動できるようにする。下に最近の調査3件とライブラリへのリンクを置く。資料全件の大きな表をホームへ重ねない。
- **保有・推移**：親メニューは保持し、「資産サマリー」（`#a/summary`）、「資産推移」（`#a/all`）、「保有一覧」（`#a/holdings`）、「全体方針」（`#a/policy`）を切り替える。サマリーは総資産・前週差・クラス別／口座別構成・今週の増減、保有一覧はクラス別の明細表、全体方針は従来の非公開stateのMarkdown。数値や集計方法は共通のまま。
- **資産推移（`#a/all`）**：期間セレクタ、積み上げ／折れ線、クラス・銘柄チェックと推移グラフを表示する。明細表と増減一覧は専用画面へ分ける。期間・表示形式・チェックはページを移動しても保持する。
- **調査一覧パネル**（`researchPanel`）：スナップショット注記と調査一覧の表（対象・区分バッジ・最新の調査日・資料リンク・アーカイブ＝過去の調査日リンク）。`tiles: true` でテーマ数・企業数・最新調査日・資料数の `.metric` タイルを前置する。
- **資料ビューア**：見出しはコンパクト表示（`body.compact-head`）。タイトル「【調査名】資料名」と、同じ行に「区分 · 調査日 · パス」（幅が足りなければ折り返す）。資料の切り替えはサイドバーの資料一覧で行う（本文上の資料タブは置かない）。見出しの下の1行（`.viewer-meta`、狭い画面では折り返す）に、版が2つ以上ある対象では版バー（`.version-bar`：「調査の版」と日付チップ。最新に「最新」、それ以外に「アーカイブ」。別の版へ移るときは同じファイル名の資料を開き、無ければ先頭の資料）、スナップショット注記、本体。
  - アーカイブ（最新でない版）を表示中は、区分の後ろに「アーカイブ」を付け、スナップショット注記の代わりに琥珀色の `.archive-note`（「過去の調査（日付時点）をアーカイブとして表示しています」と最新版へのリンク）を出す。
  - HTML：全高の `<iframe sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads">`。読み込み後に中身の高さへ合わせ（`fitFrame`、ResizeObserverで追従）、iframe内ではなくページ全体がスクロールする。中身が表示枠の高さに追従する（100vh）ページだけは固定の高さのまま
  - Markdown：`markdown.js` で描画して `.doc` に表示
  - PDF：ブラウザのPDF表示（iframe）とダウンロードリンク
  - コード（`valuation.mjs` など）：エスケープした `<pre class="doc-code">`
- **コスト**：見出し「このシステムの維持費 · Asset Hub」、今月の予算アラート、差引費用・利用料金・クレジットのタイル、日別グラフ、サービス別内訳。GCPコンソールへのリンクはAPIが返す `project` を使う。

調査資料はすべて調査日時点のスナップショットとして表示し、現在の投資判断と混同させない（ホームと各資料に注記を置く）。

## ルーティング

| ハッシュ | 画面 | 見出し（eyebrow） | 描画先 |
| --- | --- | --- | --- |
| `#home`（既定） | ホーム（資産全体＋最近の調査） | OVERVIEW | `#homeSection` |
| `#a/all` | 保有・推移（全資産）。`#a/policy` は全体方針、他の `#a/<英小文字>` は保有・推移を開く | ASSETS | `#assetSection` |
| `#r/<entryId>/<itemIndex>` | 調査 `entryId` の `items[itemIndex]`。番号省略・範囲外は先頭の資料 | RESEARCH（コンパクト見出し） | `#researchSection` |
| `#cost` | コスト | COST | `#costSection` |

サイドバーの選択状態は `data-view` で合わせる。資産の集計はすべて `asset-model.js` の純粋関数（`seriesByDate` / `portfolioSummary` / `movers` / `holdings` / `researchEntryFor` / `weekRows`）で行い、サーバーは生の state を返すだけ。保有銘柄と調査の対応は、同じ資産クラスのグループにある最新エントリのうち `code === symbol` か slug が `<symbol>-` で始まるもの。

`entryId` は `research/catalog.json` の `id`（`<slug>-<調査日>`）。 1つのHTMLに複数の表示がある場合は、調査フォルダの `views.json` で名前付きの表示を定義すると、カタログは表示ごとに別の項目（`view` 付き）を作り、ビューアは `?view=<名前>` を付けてそのHTMLを開く（`catalog.js` の `itemUrl`）。版ごとに別の `entryId` を持つので、アーカイブのURLは最新版が追加されても変わらない。同じ `kind` と `slug` の調査を版として束ね、調査日が最も新しいものを最新版とする（`catalog.js` の `versionsOf`・`latestGroups`）。カタログは `GET /api/catalog`、資料本体は `GET /research/<research/以下のパス>` から読む。

## Markdownレンダラー（`web/markdown.js`）

`renderMarkdown(source, {basePath, resolveLink, fileUrl})` は文字列を返す。

- 対応：見出し（重複しないid付き）、段落、太字・斜体・取り消し線、インラインコード、コードブロック（言語名は `data-language`）、箇条書き・番号付きリスト（入れ子）、表（配置は `md-align-*` クラス）、リンク・画像、引用、区切り線。
- 安全性：すべての本文をエスケープし、Markdown内のHTMLは文字として表示する。リンクは `http(s):`・`mailto:`・相対パス・ページ内 `#` のみ許可し、それ以外（`javascript:` など）はリンクにしない。属性値も必ずエスケープする。`style` 属性は出力しない（CSPで禁止）。
- 相対リンク：Markdownファイルのフォルダを基準に解決し、カタログ内の資料なら `#r/...` へ書き換える。ルートの `README.md` は `#home`。カタログ外の `research/` 配下は新しいタブで開く。リポジトリの外に出るパスはリンクにしない。
- 外部リンク：`target="_blank" rel="noreferrer"` と「↗」。

## CSP（コンテンツセキュリティポリシー）

シェルは `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; connect-src 'self'` で配信される。

- インラインの `<script>`、`<style>`、`style="..."` 属性、`onclick` などのイベント属性を `web/` に書かない。見た目はクラスで指定する。
- 実行時の位置合わせ（グラフのツールチップ）は CSSOM（`element.style.left = ...`）で行う。これはCSPの対象外。
- 外部フォント・CDNは使わない。研究用HTMLは別CSPで配信され、iframe内で表示する。

## グラフ — 共通部品 `UiCharts`

コストの日別グラフは `UiCharts` を使う。ページにSVG描画・目盛り計算・ラベル配置・ホバー処理を追加しない。

```js
UiCharts.destroy(host);              // 再描画・非表示化の前に古い購読を破棄
host.innerHTML = UiCharts.render({
  title: '2026年10月の日別の差引費用',
  unit: 'yen', currency: 'JPY',      // 'count'（件）/ 'man'（円を万円で表示）/ 'yen'（＋currency）
  labels: 'none',
  rows: [{label: '10/1', name: '10月1日', net: 120.5}],
  series: [{key: 'net', label: '差引費用', tone: 'primary', kind: 'bar'}],
});
UiCharts.mount(host);                // host内のすべてのグラフを有効化
```

- 色は `--chart-*` だけを使い、意味で指定する（`primary`＝実績・測定値、`secondary`＝2つ目の測定値、`target`＝計画、`accent`＝補助、`negative`、`context`＝参考）。
- 構成比・積み上げはカテゴリ色 `cat-1`〜`cat-6` を系列順に固定して使う（`tone: 'cat-1'` → `.ui-chart-tone-cat-1` → `--chart-cat-1`）。意味色と混ぜない。隣り合う番号はコントラストが付くよう並べてあるので、順番を飛ばさない。
- 軸・凡例は10.5px、値は10px。1 SVG単位＝1 CSS pxでコンテナ幅に合わせて再計算する。
- 資産推移だけは `labels: 'all', labelSize: 'compact'` を指定する。値は `--chart-font-value-compact` / `--font-size-chart-value-compact` の9px。既存の費用・株価グラフの既定サイズやラベル間引きは変更しない。
- `null`/`undefined` は未確認として線を切り、0へ置換しない。
- 株価の折れ線は `unit: 'yen', currency: 'USD', includeZero: false` でドルを表示し、価格範囲に軸を合わせる。`includeZero` の既定は `true`。棒・面・積み上げは指定によらず0を含む。
- 調査の `stock-chart.html` は `/stock-chart.js` と共通 `UiCharts` を使い、保存された日次終値を表示。保存全期間・直近90日・直近30日を切り替え、日付・ドル終値・前取引日比・表示期間騰落率とデータ表を示す。SpaceXは上場以降、テスラは直近1年を保存。HTMLの `data-stock-symbol` で銘柄を指定し、`stock-chart-model.js` の対応表で銘柄・上場日・データパスを照合する（省略時SPCX）。Starlinkは独立株価を作らずSPCXの参考チャートを表示。カタログ末尾へ追加して既存資料のURL番号を維持する。

### 系列の種類と積み上げ

```js
UiCharts.render({
  title: '資産クラス別の評価額', unit: 'man', stacked: true, slot: 14,
  rows: [{label: '1/3', name: '2026年1月3日', group: '2026年', stock: 1200000, cash: 300000}],
  series: [{key: 'stock', label: '個別株', kind: 'bar', tone: 'cat-1'}, {key: 'cash', label: '現金', kind: 'bar', tone: 'cat-2'}],
});
```

- `series[].kind` は `'line'`（既定）/ `'bar'` / `'area'`。`area` は上端の線とその下の塗り（`.ui-chart-area`、`--chart-area-opacity` で半透明）を描き、点マーカーは付けない。欠損で塗りも分断する。
- `stacked: true` で全系列を系列順に積む（`kind` を問わない）。値は前系列までの累計の上に載り、目盛りは行合計で決める。**負の値は 0 として積み**、欠損はその区分を描かず合計にも入れない。棒は横並びのオフセットをなくし 1 本分の幅になる。
- 積み上げ時は値ラベルの既定が `labels: 'none'` になる（区分上のラベルは累計と読み違えるため）。必要なら `labels: 'auto'` で明示する。
- 積み上げ時のツールチップと読み上げ説明には各系列の後に `合計` 行（`.ui-chart-total`）が付く。全系列が欠損の行は `missingLabel` を表示する。
- x 軸ラベルは幅に応じて `labelEvery` 行おきに間引き、最後の行は必ず残す。`group`（年など）の区切りは間引きとは無関係に必ず表示する。`labelEvery` オプションで間引き間隔を固定できる。週次データは `slot: 14` と `group` に年を渡す。
- `stacked` は `data-chart-options` に残るので、`mount()` 後の幅再計算でも同じ積み上げで再描画される。

### 資産推移の折れ線と全点ラベル

資産ページは全体・クラス内訳とも `kind: 'line'` を使い、積み上げへの切替は置かない。カテゴリ色の各内訳に、`primary` の破線と輪郭マーカーで「選択項目の合計」を加える。1項目だけのときも合計を残し、凡例・ツールチップ・読み上げで合計であることを明記する。全解除時は空の案内にする。

`labels: 'all'` は同値・0を含む全観測点のラベルを残す。列幅を最長ラベルに合わせ、同じ週のラベルを値順に上下へ配置して重なりを避ける。大きく動かしたラベルは細い引出線で元の点へ結ぶ。系列数に応じて必要な高さを確保し、横幅不足時はグラフ内でスクロールする。日付軸の間引きと値ラベルの省略は別で、値ラベルは省略しない。`labelSize: 'compact'` の万円ラベル・ツールチップは最大小数4桁で1円単位を保持する。

クラス内訳の候補は選択期間に存在したすべての銘柄から取り、売却済みを「過去保有」と表示する。個別の未保有週は線を切り、選択合計では0円として合算する。全選択時は各週のクラス合計と照合できる。現在の保有一覧は最新スナップショットのままにする。

## トークンの使い方

新しいCSSは `tokens.css` の値を `var()` で参照する。文字サイズ・ウェイト・行間・余白・線幅・z-index・色（`#…` や `rgb()`）を直書きしない。カスタムプロパティは `tokens.css` 以外で定義しない。新しい用途が必要なら `tokens.css` とこの文書に追加する。

| 種類 | 例 |
| --- | --- |
| 文字 | `--font-size-micro`(10) / `caption`(11) / `small`(12) / `body`(13) / `section`(15) / `emphasis`(18) / `title`(22) |
| 余白 | `--space-4/8/12/16/20/24/32`（新規は4の倍数を優先） |
| 色 | `--navy`、`--navy-dark`、`--blue`、`--blue-light`、`--muted`、`--line`、`--surface`、`--nav-*`、`--warning-*`、`--danger-*`、`--chart-*` |
| グラフ | 意味色 `--chart-primary/secondary/target/accent/negative/context`、カテゴリ色 `--chart-cat-1`〜`--chart-cat-6`（既存色の参照で定義。系列順に固定）、`--chart-area-opacity`（面グラフの塗り） |
| 増減 | `--delta-up-ink`（前週比プラス＝`--blue`）、`--delta-down-ink`（マイナス＝`--chart-negative`）。資産画面の前週差・増減上位に使う（クラス `.delta-up` / `.delta-down` / `.delta-flat`、`assets.css`） |
| 形 | `--radius-small`(4) / `--radius-control`(7) / `--border-width-thin/medium/strong` |
| ビューア | `--viewer-offset`（iframeの高さ＝100vh−この値）、`--doc-max-width`（本文の最大幅） |

文字サイズは Pathosion Ops の密度にそろえる。注記・版ボタン・補足は10px、表・一覧の本文は11px、Markdown資料の本文は12px（見出しはh1 16px・h2 14px・h3 13px、表11px・表見出し10px、コード11px）。

```css
.example-card {
  padding: var(--space-12) var(--space-16);
  font-size: var(--font-size-body);
  border: var(--border-width-thin) solid var(--line);
}
```

バッジは区分ごとに固定：テーマ＝`.badge.high`（青系）、企業＝`.badge.medium`（琥珀系）。

## 移行状況

`styles.css` と `costs.css` は参照ダッシュボードの寸法をそのまま移植したCSSで、文字サイズ・余白の直書きが残る（色はトークン化済み）。一括置換せず、画面を触るときに部品単位でトークンへ移す。`app.css`・`doc.css` など新規CSSは全項目を検査する。

## 検証

```sh
python3 scripts/check_design_tokens.py
python3 scripts/build_catalog.py --check
node --test tests/*.cjs          # リポジトリのルートで実行
```

`check_design_tokens.py` は次を検出する：未定義・循環トークン、`tokens.css` 以外でのカスタムプロパティ定義、新規CSSの文字・余白・線幅・z-index・色の直書き、CSPで禁止されるインラインstyle・インラインscript・イベント属性、グラフ描画コード（`charts.js`、`cost-view.js`、`asset-view.js`）内の色・文字サイズの直書き。

`tests/test_markdown.cjs` はエスケープ・危険なリンクの拒否・相対リンクの書き換え・入れ子リスト・表を、`tests/test_costs.cjs` はコスト集計・予算判定・表示を、`tests/test_catalog.cjs` はカタログの形式とルーティングを、`tests/test_charts.cjs` はグラフ部品を、`tests/test_assets.cjs` は資産の集計（フィクスチャ `tests/fixtures/assets/`）・表示のエスケープ・`validPayload` を確認する。

見た目を変えたときは、ホーム・保有・推移（`#a/all`）・Markdown資料・HTMLダッシュボード・コストをデスクトップとスマホ幅（375px）で確認し、ページ全体の横あふれ、サイドバーの折り返し、iframeの高さを見る。

## カタログ（`research/catalog.json`）

AIサプライチェーンの最新版「EPS・PER」ビューは、[ai-valuations.js](../web/ai-valuations.js) と [ai-valuations.css](../web/ai-valuations.css) で上場全社の一覧を専用画面に表示する。選択した版の `valuation.json`・`catalog.json` の保存値だけを読み、株価・予想を取得し直さない。検索・工程・PER順で絞り込め、EPSは保存された換算後の株価通貨で表示し、原通貨と換算注記も残す。詳細は `#ai/drivers`（株価変化の要因）、`#ai/multiples`（PERの推移）、`#ai/earnings`（EPS予想・決算）に分け、[ai-detail.js](../web/ai-detail.js) が既存の保存済みHTMLから該当パネルだけを表示する。工程・企業・期間の操作は保持する。過去の版と日付別の調査ファイルは変更しない。数値・通貨・欠損・並べ替え・表示対象は [test_ai_valuations.cjs](../tests/test_ai_valuations.cjs) で検証する。

「PERの推移」の上部には [ai-actual-valuations.js](../web/ai-actual-valuations.js) で4社の実績比較と銘柄別の月次表を表示する。株価時点と資料確認日、TTM・半年年換算の定義、分割基準、独自概算の限界を表の前に示し、一時利益の注記は初期表示で開く。保存版グラフとは時点を明示して区別する。表はページ全体で縦に展開し、幅が足りない場合だけ横スクロールする。[実績表の検証](../tests/test_ai_actual_valuations.cjs) は保存済み4社×11時点の表示数値と銘柄切替を確認する。

イビデンのように特定の売却益を除く推計がある場合は、比較表へ「推計」と明記した別行を追加し、月次表の「利益基準」で実績と切り替える。実績は保持し、推計の税率仮定・除外範囲・その他の損益が残ることを表の前に示す。推計選択時は調整方法の専用資料へリンクし、銘柄変更時は実績表示へ戻す。

3つの詳細画面のサプライチェーン工程は複数選択できる。[ai-multi-chain.js](../web/ai-multi-chain.js) を保存版のiframeへ追加し、選んだ工程の企業候補を重複なく表示する。工程追加時は新しく候補に入る企業を選択し、既存企業の手動OFFは保持する。工程を外すと、残る工程に含まれない企業を除く。全解除時は選択案内と空表示に戻す。工程ボタンのDOMとキーボード焦点を維持し、企業・期間・グラフは既存の計算を利用する。[回帰検証](../tests/test_ai_multi_chain.cjs) は保存版の実データと計算スクリプトを使い、日付別の資料ファイルを変更しない。

`python3 scripts/build_catalog.py` が `research/{themes,companies}/<slug>/<調査日>/` を走査して生成する。タイトルはルート `README.md` の表の1列目、資料名は既定値と `LABEL_OVERRIDES`、PDF名は各フォルダの `README.md` のリンク文字・説明列から取る。`working/`・`qa/`・テンプレート・`*.py`・JSONデータは含めない。内容が変わらないときはファイルを書き換えない（`generatedAt` だけの差分を作らない）。新しい調査フォルダを追加したら再生成する。

## 情報の入口と資料保全

「EPSの推移」（`#ai/eps`）はPERの隣に置き、「EPS予想・決算」と分ける。[ai-eps-trend.js](../web/ai-eps-trend.js) が保存版のTTM EPSを公表済み日から表示し、実額は現地通貨ごと、指数は開始日の正のEPS＝100で比較する。0・赤字・欠損を区別し、指数化できない企業を明記する。工程・企業・期間の既存操作に追従し、開始・終了値の表を添える。計算は [ai-eps-model.js](../web/ai-eps-model.js) で行い、保存された調査データを更新しない。

[workspace.js](../web/workspace.js) はホーム、AI調査の全体像・関連レポート・出典案内、検索できる調査ライブラリを生成する。`#ai/…` は最新保存版への入口で、カタログの並びと既存 `#r/<対象>-<日付>/<番号>` は変更しない。アーカイブは従来どおり元の資料全体を表示する。

## 将来利益・割安度

「将来利益・割安度」（`#ai/forward`）は[ai-forward-ranking.js](../web/ai-forward-ranking.js)で46社の保存済み独自シナリオを表示する。年・ケース・要求年率を変えるとEPS、通常純利益、想定PER、計算価格、価格余地と並びが同じ条件へ連動する。初期は2029年・基準・年12%の計算上の価格余地順。Eatonは事業分離価値を未評価の参考行として順位比較から除外する。

表は全行を縦に展開し、横幅が足りない場合だけ横スクロール。確認範囲と成立条件を初期表示し、各行の詳細で6ケースと原典を確認できる。赤字の利益法価値はゼロにせず算出不能。順位を投資推奨順位や確率付き期待値と呼ばない。
