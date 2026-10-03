const total=(rows,key)=>rows.reduce((sum,row)=>sum+Math.round(row[key]*1e6),0)/1e6;
export function costMonths(snapshot){
 if(!snapshot?.window)return [];
 const months=[],start=new Date(snapshot.window.start+'T00:00:00Z');
 for(let date=new Date(start);date.toISOString().slice(0,10)<snapshot.window.end;date.setUTCMonth(date.getUTCMonth()+1))months.push(date.toISOString().slice(0,7));
 return months.reverse();
}
export function summarizeCosts(snapshot,month){
 const rows=(snapshot?.records||[]).filter(row=>row.date.startsWith(month));
 if(!rows.length)return {hasData:false,gross:null,credits:null,net:null,services:[],days:[]};
 const services=[...new Set(rows.map(r=>r.serviceId))].map(id=>{const group=rows.filter(r=>r.serviceId===id);return {id,name:group[0].service,gross:total(group,'gross'),credits:total(group,'credits'),net:total(group,'net')};}).sort((a,b)=>b.net-a.net||a.name.localeCompare(b.name));
 const days=[...new Set(rows.map(r=>r.date))].sort().map(date=>({date,net:total(rows.filter(r=>r.date===date),'net')}));
 return {hasData:true,gross:total(rows,'gross'),credits:total(rows,'credits'),net:total(rows,'net'),services,days};
}
export function money(value,currency='JPY'){
 return value==null?'—':new Intl.NumberFormat('ja-JP',{style:'currency',currency,minimumFractionDigits:2,maximumFractionDigits:2}).format(value);
}

// Compare this month's project-wide net cost with the notification budget.
// The existing GCP budget includes all credits; exported usage remains delayed.
export function costBudgetAlert(payload,now=new Date()){
 const month=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit'}).format(now);
 const cap=payload?.budget?.projectBudget,currency=payload?.budget?.currency;
 const rows=(payload?.snapshot?.records||[]).filter(row=>row.date.startsWith(month));
 const available=Number.isFinite(cap)&&cap>0&&currency==='JPY'&&payload?.snapshot?.currency===currency&&rows.length&&rows.every(row=>Number.isFinite(row.net));
 if(!available)return {level:'unknown',month,cap,currency,amount:null,percent:null};
 const amount=total(rows,'net'),percent=amount/cap*100;
 return {level:percent>=100?'danger':percent>=80?'warning':'normal',month,cap,currency,amount,percent};
}
