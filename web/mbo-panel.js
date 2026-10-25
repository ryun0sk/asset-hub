import {initMboApp} from './mbo-app.js';

// Asset Hub owns the sidebar, page heading and hash route. This component owns
// only its content and read-only requests, with explicit cleanup when leaving.
export function renderMboPanel() {
  return `<div class="mbo-embedded"><div class="mbo-panel-actions"><button id="mboReload" class="mbo-button" type="button">保存済み結果を再読込</button></div>
      <p id="mboDemoNotice" class="mbo-notice mbo-demo" role="note" hidden>架空デモの表示です。実在企業の評価・投資判断ではありません。</p>
      <p id="mboWeeklyNotice" class="mbo-notice">並び順は調査の作業順で、MBO確率や有力度ではありません。評価軸は設計仮説・未検証です。企業価値は独自シナリオです。相場・資料は更新せず、保存済みの時点を表示します。</p>
      <div id="mboStatus" class="mbo-status" role="status" aria-live="polite">保存した週次結果を確認しています…</div>
      <div id="mboError" class="mbo-notice mbo-error" role="alert" hidden></div>
      <section id="mboRunToolbar" class="mbo-run-toolbar" aria-label="表示する実行結果">
        <label>実行結果<select id="mboRunSelect" disabled><option value="">読み込んでいます…</option></select></label>
        <p id="mboRunMeta" class="mbo-muted"></p>
      </section>
      <section id="mboCoverage" class="mbo-metrics" aria-label="対象と確認状況"></section>
      <section id="mboCandidatesSection" aria-labelledby="mboCandidatesTitle">
        <div class="mbo-section-head"><div><h2 id="mboCandidatesTitle">調査候補</h2><p id="mboCandidateCount" class="mbo-muted"></p></div></div>
        <div class="mbo-filters">
          <label>企業・証券コード<input id="mboSearch" type="search" autocomplete="off" placeholder="企業名・コードで検索" maxlength="100"></label>
          <label>確認状態<select id="mboFilter"><option value="all">すべて</option><option value="new">新規候補</option><option value="needs_review">確認が必要</option><option value="missing_price">株価未入力</option><option value="ready">価格評価可</option></select></label>
          <label>並び順<select id="mboSort"><option value="rank">調査作業順</option><option value="discount_desc">割安率が高い順</option><option value="name">企業名順</option></select></label>
        </div>
        <div id="mboCandidates" aria-live="polite"></div>
      </section>
      <section id="mboEventsSection" aria-labelledby="mboEventsTitle" hidden>
        <div class="mbo-section-head"><div><h2 id="mboEventsTitle">公表・検討中の案件</h2><p class="mbo-muted">公表済みの案件と未発見の調査候補を分けて確認します。</p></div></div>
        <div id="mboEvents"></div>
      </section>
      <section id="mboHistorySection" aria-labelledby="mboHistoryTitle" hidden>
        <div class="mbo-section-head"><div><h2 id="mboHistoryTitle">週次の変化</h2><p class="mbo-muted">選択した実行結果と前回の保存結果を比較します。</p></div></div>
        <div id="mboDiff"></div>
        <div class="mbo-section-head"><h2>実行履歴</h2></div>
        <div id="mboRuns"></div>
      </section>
      <section id="mboCasesSection" aria-label="過去事例" hidden><div id="mboCases"></div></section>
      <section id="mboDetailSection" class="mbo-detail" aria-labelledby="mboDetailTitle" hidden>
        <div class="mbo-section-head"><h2 id="mboDetailTitle" tabindex="-1">企業の調査内容</h2><button id="mboCloseDetail" class="mbo-button" type="button">詳細を閉じる</button></div>
        <div id="mboDetail" aria-live="polite"></div>
      </section>
      <footer class="mbo-footer">資料と株価を確認した週次結果を表示します。計算はMacで実行し、原本はMac内に保存します。</footer>
      <noscript><p class="mbo-notice mbo-error">この画面の表示にはJavaScriptが必要です。</p></noscript></div>`;
}

export function mountMboPanel(host, section = 'candidates', fetcher = globalThis.fetch) {
  host.innerHTML = renderMboPanel();
  return initMboApp(host.ownerDocument, fetcher, {root: host, listenHash: false, initialView: section, embedded: true});
}
