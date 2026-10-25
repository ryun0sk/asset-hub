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
test('stock lines may omit zero, while bars, areas and default charts keep their baseline',()=>{
  const input={unit:'yen',currency:'USD',rows:[{label:'10/1',close:157.65},{label:'10/2',close:158.96}],series:[{key:'close',label:'SPCX'}]};
  assert.equal(charts.layout(input).scale.min,0);
  const stock=charts.layout({...input,includeZero:false});
  assert.ok(stock.scale.min>0&&stock.scale.min<=157.65&&stock.scale.max>=158.96);
  assert.match(charts.tooltip(input.rows[1],stock),/\$158\.96/);
  for(const kind of ['bar','area']) assert.equal(charts.layout({...input,includeZero:false,series:[{key:'close',kind}]}).scale.min,0);
  assert.equal(charts.layout({...input,includeZero:false,stacked:true}).scale.min,0);
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
test('complete compact labels retain equal values, zero and every finite observation',()=>{
  const input={title:'選択した資産',unit:'man',labels:'all',labelSize:'compact',rows:[{label:'1/3',a:10000,b:10000,total:20000},{label:'1/10',a:null,b:0,total:0},{label:'1/17',a:1,b:null,total:1}],series:[{key:'a',label:'A',tone:'cat-1'},{key:'b',label:'B',tone:'cat-2'},{key:'total',label:'選択項目の合計',dashed:true,marker:'ring'}]};
  const layout=charts.layout(input,390), html=charts.render(input);
  assert.equal(layout.labels.length,7);
  assert.equal(layout.labels.filter(label=>label.index===0&&label.text==='1万').length,2,'same amount in two holdings keeps both labels');
  assert.equal(layout.labels.filter(label=>label.index===1&&label.text==='0万').length,2,'zero is a label, missing values are not');
  assert.equal(layout.labels.filter(label=>label.index===2&&label.text==='0.0001万').length,2,'small nonzero yen amounts remain nonzero');
  assert.match(html,/ui-chart-value-compact/);
  assert.match(html,/ui-chart-label-leader/);
  assert.match(html,/ui-chart-point-ring/);
  assert.equal((html.match(/data-chart-index=/g)||[]).length,3);
  assert.match(html,/選択項目の合計 0\.0001万円/);
  assert.doesNotMatch(html,/NaN|Infinity|undefined|style=|font-size=/);
});
test('dense complete labels grow the chart and columns without thinning or overlapping labels',()=>{
  const denseSeries=Array.from({length:24},(_,i)=>({key:`s${i}`,label:`項目${i}`}));
  const denseRows=Array.from({length:52},(_,index)=>({label:`W${index+1}`,...Object.fromEntries(denseSeries.map((s,i)=>[s.key,index%2?0:5000000+i]))}));
  const input={unit:'man',labels:'all',labelSize:'compact',rows:denseRows,series:denseSeries};
  for(const available of [280,390,1100]) {
    const model=charts.layout(input,available);
    assert.equal(model.labels.length,52*24);
    assert.ok(model.width>available);
    assert.ok(model.height>charts.geometry.height);
    const maxTextWidth=Math.max(...model.labels.map(label=>label.text.length*charts.geometry.compactCharacterWidth));
    assert.ok(model.step>=maxTextWidth+charts.geometry.labelColumnGap-1e-8);
    for(let index=0;index<denseRows.length;index++) {
      const labels=model.labels.filter(label=>label.index===index).sort((a,b)=>a.y-b.y);
      assert.ok(labels[0].y>=12);
      assert.ok(labels.at(-1).y<=model.height-charts.geometry.bottom-8);
      for(let i=1;i<labels.length;i++) assert.ok(labels[i].y-labels[i-1].y>=charts.geometry.compactLabelGap-1e-8);
    }
  }
});
test('complete labels preserve missing-value line breaks and negative values',()=>{
  const input={unit:'count',labels:'all',labelSize:'compact',rows:[{label:'1',a:-2,b:0},{label:'2',a:null,b:0},{label:'3',a:3,b:null}],series:[{key:'a',label:'A'},{key:'b',label:'B'}]};
  const model=charts.layout(input);
  assert.equal(model.labels.length,4);
  assert.equal(model.labels.some(label=>label.text==='-2件'),true);
  assert.equal(model.plots[0].points[1],null);
  assert.equal(model.plots[0].path.trim().split(/(?=M)/).length,2);
});
test('complete-label opt-in leaves existing chart geometry and font classes unchanged',()=>{
  const normal={unit:'man',rows:[{label:'1',a:12345,b:12345}],series:[{key:'a',label:'A'},{key:'b',label:'B'}]};
  const model=charts.layout(normal,390), html=charts.render(normal);
  assert.equal(model.width,390);
  assert.equal(model.height,260);
  assert.equal(model.labels.length,1);
  assert.equal(model.labels[0].text,'1.23万');
  assert.doesNotMatch(html,/ui-chart-value-compact|ui-chart-label-leader/);
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
