# Asset Hub デザインシステム

Asset Hub（株式投資の調査ダッシュボード）の画面は、Pathosion Ops ダッシュボードと同じ見た目・部品の考え方で作る。ネイビーの左サイドバー、白いトップバー、`.metric` のタイル、`.panel` の表、コストタブ、共通グラフ部品をそのまま踏襲し、ロゴ画像の代わりにテキストのワードマーク「Asset Hub」を使う。文字・色・線・余白の値は `web/tokens.css` だけに置き、実行時に他リポジトリへ依存しない。ライトテーマのみ。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `web/tokens.css` | 文字サイズ・ウェイト・行間・余白・ブランド色・状態色・グラフ色・線幅・角丸。値（カスタムプロパティ）の唯一の定義場所 |
| `web/styles.css` | シェル（サイドバー・トップバー・見出し・タイル・パネル・表・バッジ）。参照ダッシュボードの寸法を移植した既存CSS |
| `web/costs.css` | コストタブ。参照ダッシュボードから移植。色はトークン化済み |
| `web/app.css` | ワードマーク、調査ナビ、ホームの一覧表、資料ビューア（iframe・コード表示）。新規CSS |
| `web/doc.css` | Markdown表示（`.doc`）。新規CSS |
| `web/charts.js` / `web/charts.css` | 共通グラフ部品 `UiCharts` と `.ui-chart*` のスタイル。ページ側で上書きしない |
| `web/markdown.js` | 安全なMarkdownレンダラー（下記） |
| `web/catalog.js` | 調査カタログの参照とハッシュルーティング（純粋関数） |
| `web/app.js` | 画面の切り替え、サイドバー、ホーム、資料ビューア |
| `web/cost-model.js` / `cost-view.js` / `costs.js` | コストの集計・表示・取得（5分ごとの再取得とサイドバー警告） |

読み込み順は `tokens.css` → `styles.css` → `charts.css` → `costs.css` → `app.css` → `doc.css`。

## 画面の構成

- **サイドバー**（幅224px、`--navy-dark`）：先頭に「ホーム」、続いて区分ラベル「テーマ」「企業」の下に各調査を `.nav-link` で並べる。選択中の調査だけ資料（ダッシュボード・レポート・README・PDFなど）を `.subnav` で展開し、選択中の資料は青い点で示す。最下部に区切り線（`.cost-nav`）付きの「コスト」タブと予算警告 `#costNavAlert`、その下にワードマーク。アイコンはLucide系の線画SVGをインラインで置く（`stroke-width` 1.7、18px表示）。
- **トップバー**：「Asset Hub / 現在の画面」のパンくず。資料表示中は右側に調査日と「新しいタブで開く」。
- **ホーム**：テーマ数・企業数・最新調査日・資料数の `.metric` タイル、スナップショット注記、調査一覧の表（対象・区分バッジ・調査日・資料リンク）。
- **資料ビューア**：見出しは区分・調査日、タイトル「【調査名】資料名」、パス。資料の切り替えはサイドバーの資料一覧で行う（本文上の資料タブは置かない）。見出しの下にスナップショット注記と本体。
  - HTML：全高の `<iframe sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads">`
  - Markdown：`markdown.js` で描画して `.doc` に表示
  - PDF：ブラウザのPDF表示（iframe）とダウンロードリンク
  - コード（`valuation.mjs` など）：エスケープした `<pre class="doc-code">`
- **コスト**：見出し「このシステムの維持費 · Asset Hub」、今月の予算アラート、差引費用・利用料金・クレジットのタイル、日別グラフ、サービス別内訳。GCPコンソールへのリンクはAPIが返す `project` を使う。

調査資料はすべて調査日時点のスナップショットとして表示し、現在の投資判断と混同させない（ホームと各資料に注記を置く）。

## ルーティング

| ハッシュ | 画面 |
| --- | --- |
| `#home`（既定） | ホーム |
| `#r/<entryId>/<itemIndex>` | 調査 `entryId` の `items[itemIndex]`。番号省略・範囲外は先頭の資料 |
| `#cost` | コスト |

`entryId` は `research/catalog.json` の `id`（`<slug>-<調査日>`）。カタログは `GET /api/catalog`、資料本体は `GET /research/<research/以下のパス>` から読む。

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
- 軸・凡例は10.5px、値は10px。1 SVG単位＝1 CSS pxでコンテナ幅に合わせて再計算する。
- `null`/`undefined` は未確認として線を切り、0へ置換しない。

## トークンの使い方

新しいCSSは `tokens.css` の値を `var()` で参照する。文字サイズ・ウェイト・行間・余白・線幅・z-index・色（`#…` や `rgb()`）を直書きしない。カスタムプロパティは `tokens.css` 以外で定義しない。新しい用途が必要なら `tokens.css` とこの文書に追加する。

| 種類 | 例 |
| --- | --- |
| 文字 | `--font-size-micro`(10) / `caption`(11) / `small`(12) / `body`(13) / `section`(15) / `emphasis`(18) / `title`(22) |
| 余白 | `--space-4/8/12/16/20/24/32`（新規は4の倍数を優先） |
| 色 | `--navy`、`--navy-dark`、`--blue`、`--blue-light`、`--muted`、`--line`、`--surface`、`--nav-*`、`--warning-*`、`--danger-*`、`--chart-*` |
| 形 | `--radius-small`(4) / `--radius-control`(7) / `--border-width-thin/medium/strong` |
| ビューア | `--viewer-offset`（iframeの高さ＝100vh−この値）、`--doc-max-width`（本文の最大幅） |

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

`check_design_tokens.py` は次を検出する：未定義・循環トークン、`tokens.css` 以外でのカスタムプロパティ定義、新規CSSの文字・余白・線幅・z-index・色の直書き、CSPで禁止されるインラインstyle・インラインscript・イベント属性、グラフ描画コード（`charts.js`、`cost-view.js`）内の色・文字サイズの直書き。

`tests/test_markdown.cjs` はエスケープ・危険なリンクの拒否・相対リンクの書き換え・入れ子リスト・表を、`tests/test_costs.cjs` はコスト集計・予算判定・表示を、`tests/test_catalog.cjs` はカタログの形式とルーティングを、`tests/test_charts.cjs` はグラフ部品を確認する。

見た目を変えたときは、ホーム・Markdown資料・HTMLダッシュボード・コストをデスクトップとスマホ幅（375px）で確認し、ページ全体の横あふれ、サイドバーの折り返し、iframeの高さを見る。

## カタログ（`research/catalog.json`）

`python3 scripts/build_catalog.py` が `research/{themes,companies}/<slug>/<調査日>/` を走査して生成する。タイトルはルート `README.md` の表の1列目、資料名は既定値と `LABEL_OVERRIDES`、PDF名は各フォルダの `README.md` のリンク文字・説明列から取る。`working/`・`qa/`・テンプレート・`*.py`・JSONデータは含めない。内容が変わらないときはファイルを書き換えない（`generatedAt` だけの差分を作らない）。新しい調査フォルダを追加したら再生成する。
