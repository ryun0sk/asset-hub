import {mountActualValuationHistory} from './ai-actual-valuations.js';

// Present a single question from the existing snapshot without changing its data or calculations.
export const AI_DETAIL_SECTIONS = Object.freeze({
  drivers: Object.freeze({
    blockId: 'val-decomp',
    title: '株価変化の要因',
    description: '選択期間の値動きを、EPS（利益）とPER（評価倍率）の寄与に分けて確認します。',
  }),
  multiples: Object.freeze({
    blockId: 'val-pe',
    title: 'PERの推移・過去比較',
    description: '4銘柄の実績EPS・PER月次表と、保存版のPERグラフを確認します。',
  }),
  earnings: Object.freeze({
    blockId: 'val-eps',
    title: 'EPSの推移・予想・決算日',
    description: '四半期・通期の利益の実績、会社予想、外部予想と、確認済みの次の決算日を確認します。',
  }),
});

const mounts = new WeakMap();
const BLOCK_IDS = ['val-now', ...Object.values(AI_DETAIL_SECTIONS).map(section => section.blockId)];

// Only apply after the expected snapshot has loaded; unfamiliar documents retain their original view.
export function applyAiDetail(doc, section = 'drivers') {
  const selected = AI_DETAIL_SECTIONS[section];
  const panel = doc.getElementById('panel-chart');
  const fundamentals = doc.getElementById('subpanel-fund');
  const picker = panel?.querySelector('.chain-picker');
  if (!selected || !doc.body || !panel || !fundamentals || !picker ||
      !fundamentals.querySelector('.fund-controls') || BLOCK_IDS.some(id => !doc.getElementById(id))) return false;

  doc.body.classList.add('ai-detail');
  doc.body.dataset.aiDetail = section;
  for (const id of ['panel-map', 'panel-guide', 'subpanel-price']) {
    const element = doc.getElementById(id);
    if (element) element.hidden = true;
  }
  for (const element of doc.querySelectorAll('body > header, body > footer, main > .method, #panel-chart > .sectionhead, .fundamental-intro')) element.hidden = true;
  panel.hidden = false;
  fundamentals.hidden = false;
  for (const id of BLOCK_IDS) doc.getElementById(id).hidden = id !== selected.blockId;
  const actualHistory = doc.getElementById('ai-actual-history');
  if (actualHistory) actualHistory.hidden = section !== 'multiples';
  panel.setAttribute('aria-label', selected.title);

  let heading = doc.getElementById('ai-detail-heading');
  if (!heading) {
    heading = doc.createElement('div');
    heading.id = 'ai-detail-heading';
    heading.className = 'ai-detail-heading';
    const title = doc.createElement('h2');
    title.id = 'ai-detail-title';
    const description = doc.createElement('p');
    heading.append(title, description);
    panel.insertBefore(heading, picker);
  }
  heading.querySelector('h2').textContent = selected.title;
  heading.querySelector('p').textContent = selected.description;
  return true;
}

// Register before setting the iframe src. Remounting the same frame replaces its listener.
export function mountAiDetail(frame, section = 'drivers') {
  mounts.get(frame)?.();
  if (!AI_DETAIL_SECTIONS[section]) return () => {};
  let active = true;
  let pendingResize = null;
  let loadedStyle = null;
  let historyCleanup = null;
  let pickerScript = null;
  let pickerReady = null;
  let pickerCleanup = null;
  const resize = () => {
    if (!active) return;
    const view = frame.contentWindow;
    if (!view) return;
    if (pendingResize != null) view.cancelAnimationFrame(pendingResize);
    pendingResize = view.requestAnimationFrame(() => {
      pendingResize = null;
      if (active) view.dispatchEvent(new view.Event('resize'));
    });
  };
  const load = () => {
    if (!active) return;
    let doc;
    try { doc = frame.contentDocument; } catch { return; }
    if (!doc || !applyAiDetail(doc, section)) return;
    pickerCleanup?.();
    pickerCleanup = null;
    if (pickerScript) {
      pickerScript.removeEventListener('load', pickerReady);
      pickerScript.remove();
    }
    // The classic script runs in the snapshot's realm, so its existing lexical
    // chart state can be reused without eval or rewriting dated research files.
    pickerScript = doc.createElement('script');
    pickerScript.src = '/ai-multi-chain.js';
    pickerScript.async = false;
    pickerScript.dataset.aiMultiChainScript = '';
    pickerReady = () => {
      if (!active || doc !== frame.contentDocument) return;
      const api = frame.contentWindow?.ASSET_MULTI_CHAIN;
      if (!api?.getState || !api?.cleanup) return;
      const hint = doc.querySelector('.chain-picker-head span');
      const originalHint = hint?.textContent;
      const updateHint = () => {
        if (hint) hint.textContent = api.getState().selectedGroups.length
          ? '複数選択可 · 企業は下のチェックで選択'
          : '工程を1つ以上選んでください（複数選択可）';
      };
      const click = event => {
        if (event.target.closest?.('[data-chain]')) updateHint();
      };
      updateHint();
      doc.addEventListener('click', click);
      pickerCleanup = () => {
        doc.removeEventListener('click', click);
        if (hint) hint.textContent = originalHint;
        if (frame.contentWindow?.ASSET_MULTI_CHAIN === api) api.cleanup();
      };
      resize();
    };
    pickerScript.addEventListener('load', pickerReady);
    doc.head.append(pickerScript);
    historyCleanup?.();
    historyCleanup = null;
    if (section === 'multiples') {
      let history = doc.getElementById('ai-actual-history');
      if (!history) {
        history = doc.createElement('section');
        history.id = 'ai-actual-history';
        history.className = 'ai-actual-history';
        history.setAttribute('aria-labelledby', 'ai-actual-title');
        const panel = doc.getElementById('panel-chart');
        panel.insertBefore(history, panel.querySelector('.chain-picker'));
      }
      historyCleanup = mountActualValuationHistory(history, doc);
    }
    let style = doc.querySelector('link[data-ai-detail-style]');
    if (!style) {
      style = doc.createElement('link');
      style.rel = 'stylesheet';
      style.href = '/ai-detail.css';
      style.dataset.aiDetailStyle = '';
      doc.head.append(style);
    }
    if (loadedStyle) loadedStyle.removeEventListener('load', resize);
    loadedStyle = style;
    style.addEventListener('load', resize);
    resize();
  };
  const cleanup = () => {
    active = false;
    frame.removeEventListener('load', load);
    loadedStyle?.removeEventListener('load', resize);
    historyCleanup?.();
    pickerCleanup?.();
    pickerScript?.removeEventListener('load', pickerReady);
    pickerScript?.remove();
    if (pendingResize != null) frame.contentWindow?.cancelAnimationFrame(pendingResize);
    if (mounts.get(frame) === cleanup) mounts.delete(frame);
  };
  mounts.set(frame, cleanup);
  frame.addEventListener('load', load);
  if (frame.contentDocument?.readyState === 'complete') load();
  return cleanup;
}
