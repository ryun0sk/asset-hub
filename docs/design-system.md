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
| `web/catalog.js` | 調査カタログの参照とハッシュルーティング（純粋関数） |
| `web/app.js` | 画面の切り替え、サイドバー、調査一覧パネル（`researchPanel`）、資料ビューア |
| `web/cost-model.js` / `cost-view.js` / `costs.js` | コストの集計・表示・取得（5分ごとの再取得とサイドバー警告） |
| `web/asset-model.js` / `asset-view.js` / `assets.js` | 資産の集計（純粋関数）・表示（HTML文字列）・取得（`/api/assets`、60秒TTL、タブ復帰時に再取得。ポーリングなし） |

読み込み順は `tokens.css` → `styles.css` → `charts.css` → `costs.css` → `assets.css` → `app.css` → `doc.css`。

## 画面の構成

- **サイドバー**（幅224px、`--navy-dark`）：先頭に「ホーム」と「保有・推移」（`data-view="asset"`、資産は全部このタブ1つ）、続いて調査をテーマ・企業などの区分ラベル（`.nav-label`）ごとに並べる（`#classNav`。各対象の**最新の調査**を `.nav-link[data-target]` で並べ、過去の調査はアーカイブとして版バーから開く）。選択中の対象だけ、表示中の版の資料を `.subnav` で展開し、選択中の資料は青い点で示す。最下部に区切り線（`.cost-nav`）付きの「コスト」タブと予算警告 `#costNavAlert`、その下にワードマーク。アイコンはLucide系の線画SVGをインラインで置く（`stroke-width` 1.7、18px表示）。
- **トップバー**：「Asset Hub / 現在の画面」のパンくず。資料表示中は右側に調査日と「新しいタブで開く」。
- **ホーム（資産全体）**：`.metric` タイル（総資産・前週比（`--delta-up-ink` / `--delta-down-ink`）・記録週数・最終記録日）、表示期間セレクタ `#asset-range`（直近26週 / 52週 / 全期間）、総資産の線グラフ、クラス別の**積み上げ棒**（`cat-1`〜 を `CLASS_ORDER` 順に固定）、口座別の積み上げ棒、今週の増減（銘柄別の上位・下位。調査があれば `#r/...` へリンク、新規・売却はタグ）、最近の調査（`researchPanel`、新しい順に5件）、注記「各サイト表示の円換算評価額を週次で手入力した記録。為替・税金は未考慮」。state が無い（`status.status === 'not_configured'`）ときは `/weekly-assets` で記録するよう促す空状態。
- **保有・推移（`#a/all`）**：全資産を1ページに表示する。上からタイル（総資産・前週比・記録週数・最終記録日）、ツールバー（表示期間セレクタ `#asset-range`、表示形式ラジオ＝積み上げ／折れ線）、**資産全体の推移**（資産クラスごとのチェックボックス `.asset-check` で表示するクラスを選ぶ。折れ線では選択の合計を破線で足す）、今週の増減、**資産ごとの内訳**（クラスごとのパネル。銘柄ごとのチェックボックスでそのクラスのグラフに出す銘柄を選び、下に保有一覧を置く。評価損益は `costJpy` がある行だけ）。チェック・期間・表示形式の選択は `assets.js` が保持し、再描画後もフォーカスを同じ入力に戻す。ホームは元どおり調査一覧で、資産の画面は持たない。
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
| `#a/all` | 保有・推移（全資産）。`#a/<英小文字>` はどれも同じページを開く | ASSETS | `#assetSection` |
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
- `null`/`undefined` は未確認として線を切り、0へ置換しない。

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

`python3 scripts/build_catalog.py` が `research/{themes,companies}/<slug>/<調査日>/` を走査して生成する。タイトルはルート `README.md` の表の1列目、資料名は既定値と `LABEL_OVERRIDES`、PDF名は各フォルダの `README.md` のリンク文字・説明列から取る。`working/`・`qa/`・テンプレート・`*.py`・JSONデータは含めない。内容が変わらないときはファイルを書き換えない（`generatedAt` だけの差分を作らない）。新しい調査フォルダを追加したら再生成する。
