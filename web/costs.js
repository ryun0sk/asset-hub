import {costView} from './cost-view.js';
import {costBudgetAlert} from './cost-model.js';
import {UiCharts} from './charts.js';
let payload=null,loading=false,error='',month='',loadedAt=0;
const root=()=>document.getElementById('costSection');
// Accept whatever project the server reports (null until billing is configured);
// only the payload shape is checked.
export const validPayload=next=>Boolean(next&&typeof next==='object'&&(next.project==null||typeof next.project==='string')&&next.syncStatus&&typeof next.syncStatus==='object');
function render(){
  const badge=document.getElementById('costNavAlert'),alert=costBudgetAlert(payload);
  if(badge){
    const warning=['warning','danger'].includes(alert.level);
    badge.hidden=!warning;
    badge.textContent=warning?'⚠':'';
    badge.className='cost-nav-alert cost-nav-alert-'+alert.level;
    badge.setAttribute('aria-label',alert.level==='danger'?'今月のプロジェクト全体の費用が通知用予算以上':'今月のプロジェクト全体の費用が通知用予算の80%以上');
    badge.title=badge.getAttribute('aria-label')+'（取得済み明細の目安）';
  }
  const host=root();
  if(!host||host.hidden)return;
  UiCharts.destroy(host);
  host.innerHTML=costView(payload,{loading,error,month});
  UiCharts.mount(host);
  host.querySelectorAll('[data-action="cost-reload"]').forEach(button=>button.onclick=()=>load());
  const select=host.querySelector('#cost-month');
  if(select)select.onchange=()=>{month=select.value;render();host.querySelector('#cost-month').focus();};
}
async function load(){
  if(loading)return;
  loading=true;error='';render();
  try{
    const response=await fetch('/api/costs');
    if(!response.ok)throw Error();
    const next=await response.json();
    if(!validPayload(next))throw Error();
    payload=next;loadedAt=Date.now();
  }catch{error='費用データを読み込めませんでした。前回の表示を保持しています。';}
  finally{loading=false;render();}
}
export function showCosts(){
  if(!payload||Date.now()-loadedAt>60000)load();else render();
}
export function initCostAlerts(){
  load();
  // Read the cached snapshot only; the server never starts a billing query for this.
  setInterval(()=>{if(!document.hidden)load();},5*60*1000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&Date.now()-loadedAt>60000)load();});
}
