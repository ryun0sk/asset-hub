import {costMonths,summarizeCosts,money,costBudgetAlert} from './cost-model.js';
import {UiCharts} from './charts.js';
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const time=value=>value?new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',dateStyle:'short',timeStyle:'short'}).format(new Date(value)):'—';
// GCP console link for the billing account of the project named in the payload.
export function billingUrl(project){
 return project?`https://console.cloud.google.com/billing/linkedaccount?project=${encodeURIComponent(project)}`:'https://console.cloud.google.com/billing';
}
export function costView(payload,{loading=false,error='',month=''}={}){
 const snapshot=payload?.snapshot,status=payload?.syncStatus?.status,months=costMonths(snapshot),selected=months.includes(month)?month:months[0],summary=summarizeCosts(snapshot,selected||''),currency=snapshot?.currency||'JPY';
 const messages={not_configured:'GCPの費用データ連携を設定中です。取得前の費用は「0円」として表示しません。',pending:'GCPからの初回費用データを待っています。初回反映には数時間かかることがあります。時間をおいて「表示を更新」でご確認ください。',error:'費用データの取得に失敗しました。前回取得したデータがある場合は、その内容を表示しています。'};
 const stale=snapshot&&Date.now()-Date.parse(snapshot.fetchedAt)>3*24*3600000;
 return `<section class="cost-page"><div class="cost-heading"><div><p>このシステムの維持費 · Asset Hub</p></div><button class="button" data-action="cost-reload" ${loading?'disabled':''}>${loading?'取得中…':'表示を更新'}</button></div>
 ${loading?'<div class="sync-progress" role="status"><span class="sync-spinner" aria-hidden="true"></span>費用データを読み込んでいます…</div>':''}
 ${error?`<div class="notice" role="alert">${esc(error)} <button class="button small" data-action="cost-reload">再読み込み</button></div>`:''}
 ${messages[status]?`<div class="notice" role="status">${messages[status]}</div>`:''}
 ${budgetNotice(payload)}
 ${stale?'<div class="notice" role="status">費用データの更新が遅れています。最終取得日時をご確認ください。</div>':''}
 <div class="cost-toolbar"><label>対象月 <select id="cost-month" ${months.length?'':'disabled'} aria-label="費用の対象月">${months.length?months.map(m=>`<option value="${m}" ${m===selected?'selected':''}>${m.replace('-','年')}月</option>`).join(''):'<option>データ待ち</option>'}</select></label><span>最終取得 ${time(snapshot?.fetchedAt)}（日本時間）</span></div>
 <div class="cost-metrics">${[['差引費用',summary.net,'無料枠・クレジット適用後'],['利用料金',summary.gross,'クレジット適用前'],['無料枠・クレジット',summary.credits,'割引・無料トライアルなど']].map(([label,value,note],i)=>`<section class="panel cost-metric ${i===0?'cost-metric-total':''}"><span>${label}</span><strong>${money(value,currency)}</strong><small>${note}</small></section>`).join('')}</div>
 <div class="cost-grid"><section class="panel cost-chart-panel"><h2>日別の費用</h2><p class="cost-subtitle">差引費用 · 日付にカーソルを合わせると金額を表示</p>${summary.hasData?dailyChart(summary.days,currency,selected):'<div class="cost-empty">この月の費用データはまだありません。</div>'}</section>
 <section class="panel cost-services"><h2>サービス別内訳</h2><div class="table-scroll" tabindex="0" role="region" aria-label="サービス別費用。横スクロールで内訳を確認"><table><thead><tr><th>サービス</th><th class="numeric">利用料金</th><th class="numeric">クレジット</th><th class="numeric">差引費用</th></tr></thead><tbody>${summary.services.map(service=>`<tr><td>${esc(service.name)}</td><td class="numeric">${money(service.gross,currency)}</td><td class="numeric">${money(service.credits,currency)}</td><td class="numeric">${money(service.net,currency)}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">費用データ待ち</td></tr>'}</tbody>${summary.hasData?`<tfoot><tr><th>合計</th><th class="numeric">${money(summary.gross,currency)}</th><th class="numeric">${money(summary.credits,currency)}</th><th class="numeric">${money(summary.net,currency)}</th></tr></tfoot>`:''}</table></div></section></div>
 <div class="cost-footnote"><p>GCPの利用明細は毎日1回（日本時間1時）取り込みます。最新の利用分には反映まで時間がかかるため、確定請求額とは異なる場合があります。</p><p>Asset Hub専用GCPプロジェクト${payload?.project?`（${esc(payload.project)}）`:''}の費用です。実行端末の費用、請求先全体の税金・サポート費は含みません。</p>${snapshot?.latestUsageDate?`<p>明細の最新利用日: ${esc(snapshot.latestUsageDate)} / GCP明細の更新: ${time(snapshot.latestExportAt)}（日本時間）</p>`:''}<a class="source-link" href="${esc(billingUrl(payload?.project))}" target="_blank" rel="noopener noreferrer">GCPのお支払いを確認 ↗</a></div></section>`;
}
function dailyChart(days,currency,month){
 const rows=days.map(day=>{const [,m,d]=day.date.split('-').map(Number);return {label:`${m}/${d}`,name:`${m}月${d}日`,net:day.net};});
 return UiCharts.render({title:`${month.replace('-','年')}月の日別の差引費用`,unit:'yen',currency,labels:'none',rows,series:[{key:'net',label:'差引費用',tone:'primary',kind:'bar'}]});
}

export function budgetNotice(payload){
 const alert=costBudgetAlert(payload),{level,month,cap,currency,amount,percent}=alert;
 const labels={unknown:'予算への接近状況は未確認です',normal:'プロジェクト全体の通知用予算',warning:'プロジェクト全体の通知用予算に近づいています',danger:'取得済み明細がプロジェクト全体の通知用予算以上です'};
 return `<section class="cost-budget cost-budget-${level}" role="status" aria-label="今月の予算アラート"><strong>${level==='warning'||level==='danger'?'⚠ ':''}${labels[level]}</strong><p>${month.replace('-','年')}月 · ${amount===null?'費用データ待ち':`差引費用 ${money(amount,currency)}`} / 通知用予算 ${Number.isFinite(cap)?money(cap,currency):'未取得'}${percent===null?'':`（${Math.floor(percent)}%）`}</p><p>今月のプロジェクト全体の費用（無料枠・クレジット適用後）を対象に、予算の80%以上で警告します。対象月の選択にかかわらず今月を判定します。</p><small>1日1回取得する遅延データによる目安です。最新の利用分は未反映の場合があります。この予算では自動停止しません。${payload?.syncStatus?.status==='error'?' 取得に失敗しているため、前回値を表示しています。':''}</small></section>`;
}
