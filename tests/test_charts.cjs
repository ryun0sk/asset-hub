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
test('stacked bars sit on each other in series order and the scale covers the row total',()=>{
  const stackRows=[{label:'1月',name:'1月',a:3,b:4},{label:'2月',name:'2月',a:-2,b:5},{label:'3月',name:'3月',a:null,b:2}];
  const stackSeries=[{key:'a',label:'A',kind:'bar',tone:'cat-1'},{key:'b',label:'B',kind:'bar',tone:'cat-2'}];
  const layout=charts.layout({unit:'count',stacked:true,rows:stackRows,series:stackSeries},600);
  const [a,b]=layout.plots;
  assert.ok(layout.scale.max>=7);
  // Segment 2 starts exactly where segment 1 ends, and both share the row centre (no side-by-side offset).
  assert.ok(Math.abs(b.points[0].y0-a.points[0].y)<1e-9);assert.ok(Math.abs(a.points[0].y0-layout.y(0))<1e-9);
  assert.equal(a.points[0].x,b.points[0].x);assert.equal(a.points[0].x,layout.x(0));
  // Negative values add nothing to the stack; a missing value leaves no segment and no base.
  assert.equal(a.points[1].y,a.points[1].y0);assert.ok(Math.abs(b.points[1].y0-layout.y(0))<1e-9);
  assert.equal(a.points[2],null);assert.ok(Math.abs(b.points[2].y0-layout.y(0))<1e-9);
  const html=charts.render({title:'構成',unit:'count',stacked:true,rows:stackRows,series:stackSeries});
  const rects=[...html.matchAll(/<rect class="ui-chart-bar ui-chart-tone-(cat-\d)" x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"/g)].map(m=>({tone:m[1],x:Number(m[2]),y:Number(m[3]),w:Number(m[4]),h:Number(m[5])}));
  const first=rects.filter(r=>r.x===rects[0].x);
  assert.deepEqual(first.map(r=>r.tone),['cat-1','cat-2']);
  assert.ok(Math.abs((first[1].y+first[1].h)-first[0].y)<1e-9);
  assert.equal(rects.length,4);
  assert.match(html,/ui-chart-tone-cat-1/);assert.match(html,/ui-chart-tone-cat-2/);
  assert.doesNotMatch(html,/#[0-9a-f]{3,6}|fill="|stroke="|font-size|style=/i);assert.doesNotMatch(html,/NaN|Infinity|undefined/);
});
test('stacked charts list a 合計 row in the tooltip and description and default to no value labels',()=>{
  const stackRows=[{label:'1月',name:'1月',a:3,b:4},{label:'2月',name:'2月',a:-2,b:5},{label:'3月',name:'3月',a:null,b:null}];
  const stackSeries=[{key:'a',label:'A',kind:'bar'},{key:'b',label:'B',kind:'bar'}];
  const layout=charts.layout({unit:'count',stacked:true,rows:stackRows,series:stackSeries,missingLabel:'—'});
  assert.equal(layout.labels.length,0);
  assert.ok(charts.layout({unit:'count',stacked:true,labels:'auto',rows:stackRows,series:stackSeries}).labels.length>0);
  assert.match(charts.tooltip(stackRows[0],layout),/<div class="ui-chart-total"><span>合計<\/span><b>7件<\/b><\/div>$/);
  assert.match(charts.tooltip(stackRows[1],layout),/合計<\/span><b>5件/);
  assert.match(charts.tooltip(stackRows[2],layout),/合計<\/span><b>—</);
  const html=charts.render({title:'構成',unit:'count',stacked:true,rows:stackRows,series:stackSeries,missingLabel:'—'});
  assert.match(html,/aria-label="1月 A 3件、B 4件、合計 7件"/);
  assert.match(html,/data-chart-options="[^"]*&quot;stacked&quot;:true/);
  assert.doesNotMatch(chart(),/合計|ui-chart-total|ui-chart-area/);
});
test('area series close their fill back to the base and split at missing values',()=>{
  const areaRows=[{label:'1',v:2},{label:'2',v:3},{label:'3',v:null},{label:'4',v:1},{label:'5',v:2}];
  const html=charts.render({title:'面',unit:'count',rows:areaRows,series:[{key:'v',label:'V',kind:'area',tone:'cat-3'}]});
  const area=html.match(/<path class="ui-chart-area ui-chart-tone-cat-3" d="([^"]*)"/)[1].trim();
  assert.ok(area.endsWith('Z'));
  assert.equal(area.split(/(?=M)/).length,2);assert.equal((area.match(/Z/g)||[]).length,2);
  assert.match(html,/<path class="ui-chart-area[^>]*\/><path class="ui-chart-line ui-chart-tone-cat-3"/);
  assert.doesNotMatch(html,/ui-chart-point/);
  assert.match(html,/ui-chart-key-area ui-chart-tone-cat-3/);
  assert.doesNotMatch(html,/#[0-9a-f]{3,6}|fill="|stroke="|font-size|style=/i);
  // Unstacked areas rest on the zero line; stacked areas rest on the series below.
  const single=charts.layout({unit:'count',rows:areaRows,series:[{key:'v',label:'V',kind:'area'}]});
  assert.ok(Math.abs(single.plots[0].points[0].y0-single.y(0))<1e-9);
  const stacked=charts.layout({unit:'count',stacked:true,rows:[{label:'1',a:2,b:3},{label:'2',a:1,b:1}],series:[{key:'a',label:'A',kind:'area'},{key:'b',label:'B',kind:'area'}]});
  assert.equal(stacked.plots[1].points[0].y0,stacked.plots[0].points[0].y);
  assert.ok(stacked.scale.max>=5);
  const d=stacked.plots[1].area.trim();
  assert.ok(d.startsWith('M')&&d.endsWith('Z'));
  assert.ok(d.includes(`${stacked.x(1)},${stacked.plots[0].points[1].y}`));
});
test('weekly rows thin their axis labels and keep the last one, and labelEvery can be forced',()=>{
  const weeks=Array.from({length:52},(_,i)=>({label:`W${i+1}`,name:`第${i+1}週`,group:i<20?'2025年':'2026年',v:100+i}));
  const layout=charts.layout({unit:'man',slot:14,rows:weeks,series:[{key:'v',label:'V',kind:'bar'}]},400);
  assert.ok(layout.labelEvery>1);
  const html=charts.render({title:'週次',unit:'man',slot:14,rows:weeks,series:[{key:'v',label:'V',kind:'bar'}]});
  const axis=[...html.matchAll(/<text class="ui-chart-axis" x="[^"]+" y="[^"]+" text-anchor="middle">(W\d+)<\/text>/g)].map(m=>m[1]);
  assert.equal(axis[axis.length-1],'W52');assert.ok(axis.length<52&&axis.length>1);
  assert.equal((html.match(/ui-chart-group/g)||[]).length,2);
  assert.equal(charts.layout({unit:'man',slot:14,labelEvery:4,rows:weeks,series:[{key:'v',label:'V'}]},400).labelEvery,4);
  assert.equal(charts.layout({unit:'man',slot:14,labelEvery:0,rows:weeks,series:[{key:'v',label:'V'}]},400).labelEvery,layout.labelEvery);
});
