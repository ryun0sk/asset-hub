const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context=vm.createContext({Intl,Date,Math});
vm.runInContext(fs.readFileSync('web/charts.js','utf8').replace(/^export /gm,''),context);
const {UiCharts:charts}=vm.runInContext('({UiCharts})',context);
const rows=[{label:'8月',group:'2026年',name:'2026年8月',target:2,actual:1},{label:'9月',name:'2026年9月',target:2,actual:null},{label:'10月',name:'2026年10月',target:2,actual:0}];
const series=[{key:'target',label:'目標',tone:'target',dashed:true,marker:'ring'},{key:'actual',label:'実績',tone:'primary'}];
const chart=(extra={})=>charts.render({title:'受注件数',unit:'count',rows,series,missingLabel:'—',...extra});

test('renders tokens-only markup with legend, unit and one hit target per row',()=>{
  const html=chart();
  assert.match(html,/class="ui-chart"/);assert.match(html,/単位：件/);
  assert.equal((html.match(/data-chart-index=/g)||[]).length,3);
  assert.doesNotMatch(html,/#[0-9a-f]{3,6}|fill="|stroke="|font-size/i);
  assert.doesNotMatch(html,/NaN|Infinity|undefined/);
});
test('missing values break the line and read as the missing label, 0 stays a value',()=>{
  const html=chart();
  const actual=html.match(/<path class="ui-chart-line ui-chart-tone-primary"[^>]*d="([^"]*)"/)[1].trim().split(/(?=[ML])/);
  assert.equal(actual.length,2);assert.ok(actual.every(part=>part.startsWith('M')));
  assert.match(html,/9月 目標 2件、実績 —/);assert.match(html,/10月 目標 2件、実績 0件/);
});
test('empty data and unknown options fall back safely',()=>{
  assert.match(charts.render({title:'x',rows:[{label:'1月',a:null}],series:[{key:'a',label:'A'}],emptyText:'なし'}),/role="status">なし/);
  const html=charts.render({title:'x',unit:'nope',rows:[{label:'1月',a:3}],series:[{key:'a',label:'A',tone:'nope',kind:'nope'}]});
  assert.match(html,/ui-chart-tone-primary/);assert.match(html,/単位：件/);
});
test('text is escaped in titles, labels and tooltip content',()=>{
  const html=charts.render({title:'<b>t</b>',rows:[{label:'<i>',name:'<img src=x>',a:1}],series:[{key:'a',label:'<script>'}]});
  assert.doesNotMatch(html,/<b>t|<img|<script>|<i>/);
  assert.doesNotMatch(charts.tooltip({name:'<u>',a:1},charts.layout({rows:[{a:1}],series:[{key:'a',label:'<s>'}]})),/<u>|<s>/);
});
test('scales are nice, include zero and negative values, and keep counts whole',()=>{
  const count=charts.domain([0,3],{integer:true,minimumRange:4});
  assert.ok(count.ticks.every(Number.isInteger));assert.ok(count.max>=3);
  const negative=charts.domain([-20,5],{minimumRange:1});
  assert.ok(negative.min<=-20&&negative.max>=5&&negative.ticks.includes(0));
  assert.equal(charts.domain([],{minimumRange:1}).ticks.length>1,true);
});
test('width follows the container and grows with rows, thinning axis labels when dense',()=>{
  const many=Array.from({length:30},(_,i)=>({label:`9/${i+1}`,net:i}));
  const layout=charts.layout({unit:'yen',rows:many,series:[{key:'net',label:'差引',kind:'bar'}]},400);
  assert.ok(layout.width>400);assert.ok(layout.barWidth>=3);
  const narrow=charts.layout({unit:'yen',rows:many,series:[{key:'net',label:'差引',kind:'line'}],slot:20},400);
  assert.ok(narrow.labelEvery>1);
  assert.equal(charts.layout({rows,series,unit:'count'},900).width,900);
});
test('money units format exact values in the requested currency',()=>{
  const html=charts.render({title:'費用',unit:'yen',currency:'JPY',rows:[{label:'9/1',name:'9月1日',net:12.345}],series:[{key:'net',label:'差引'}]});
  assert.match(html,/9月1日 差引 ￥12\.35/);assert.match(html,/単位：円/);
  assert.match(charts.render({title:'万',unit:'man',rows:[{label:'1月',v:1250000}],series:[{key:'v',label:'V'}]}),/125万円/);
});
test('shared values keep a single label while every series stays in the tooltip',()=>{
  const layout=charts.layout({unit:'count',rows:[{label:'1月',a:2,b:2}],series:[{key:'a',label:'A'},{key:'b',label:'B'}]});
  assert.equal(layout.labels.length,1);
  assert.equal(charts.layout({unit:'count',labels:'none',rows:[{label:'1月',a:2}],series:[{key:'a',label:'A'}]}).labels.length,0);
});
