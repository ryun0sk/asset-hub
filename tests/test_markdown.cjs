const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const load = () => import(pathToFileURL(path.join(__dirname, '..', 'web', 'markdown.js')).href);
const base = 'research/themes/demo/2026-09-05/report.md';
const routes = {
  'research/themes/demo/2026-09-05/index.html': '#r/demo-2026-09-05/0',
  'research/companies/1234-x/2026-09-05/README.md': '#r/1234-x-2026-09-05/1',
  'README.md': '#home',
};
const options = {basePath: base, resolveLink: p => routes[p] || null, fileUrl: p => p.startsWith('research/') ? '/' + p : null};

test('escapes raw HTML everywhere, including attributes, code and tables', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('<script>alert(1)</script>\n\n# <img src=x onerror=alert(1)>\n\n`<b>`\n\n| a | b |\n|---|---|\n| <i>x</i> | "q" |\n\n```html\n<div onclick="x">\n```', options);
  assert.doesNotMatch(html, /<script|<img|<i>|<div onclick|<b>/);
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html, /<code>&lt;b&gt;<\/code>/);
  assert.match(html, /<pre class="md-code" data-language="html"><code>&lt;div onclick=&quot;x&quot;&gt;<\/code><\/pre>/);
  assert.match(html, /<td>&quot;q&quot;<\/td>/);
});

test('rejects unsafe link schemes and keeps quotes out of attributes', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('[a](javascript:alert(1)) [b](data:text/html,x) [c](//evil.example) [d](https://ok.example/?q="x")', options);
  assert.doesNotMatch(html, /href="javascript|href="data|href="\/\/evil/);
  assert.equal((html.match(/md-link-disabled/g) || []).length, 3);
  assert.match(html, /href="https:\/\/ok\.example\/\?q=&quot;x&quot;" target="_blank" rel="noreferrer"/);
});

test('relative links resolve against the file and become in-app routes when catalogued', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('[dash](index.html) [co](../../../companies/1234-x/2026-09-05/README.md) [all](../../../../README.md) [data](prices.json) [up](../../../../../etc/passwd) [h](#結論)', options);
  assert.match(html, /<a href="#r\/demo-2026-09-05\/0">dash<\/a>/);
  assert.match(html, /<a href="#r\/1234-x-2026-09-05\/1">co<\/a>/);
  assert.match(html, /<a href="#home">all<\/a>/);
  assert.match(html, /<a href="\/research\/themes\/demo\/2026-09-05\/prices\.json" target="_blank" rel="noreferrer">data<\/a>/);
  assert.match(html, /<span class="md-link-disabled">up<\/span>/);
  assert.match(html, /<a href="#" data-doc-anchor="md-結論">h<\/a>/);
});

test('external links open in a new tab without a referrer; bare URLs are linked', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('出典：https://example.com/a_b_c。 [X](https://x.com/a "t")', options);
  assert.match(html, /<a href="https:\/\/example\.com\/a_b_c" target="_blank" rel="noreferrer">https:\/\/example\.com\/a_b_c<span class="md-external" aria-hidden="true">↗<\/span><\/a>。/);
  assert.match(html, /<a href="https:\/\/x\.com\/a" target="_blank" rel="noreferrer" title="t">X/);
  assert.doesNotMatch(html, /<em>/);
});

test('headings, emphasis, blockquote, rule and paragraphs', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('# 見出し A\n\n## 見出し A\n\n**太字** と *斜体* と ~~取消~~、snake_case_name\n次の行\n\n> 引用\n> 続き\n\n---', options);
  assert.match(html, /<h1 id="md-見出し-a">見出し A<\/h1>/);
  assert.match(html, /<h2 id="md-見出し-a-2">/);
  assert.match(html, /<strong>太字<\/strong> と <em>斜体<\/em> と <del>取消<\/del>、snake_case_name\n次の行/);
  assert.match(html, /<blockquote><p>引用\n続き<\/p><\/blockquote>/);
  assert.match(html, /<hr>/);
});

test('nested and ordered lists', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('- a\n  - a1\n    - a1x\n  - a2\n- b\n  continued\n\n3. three\n4. four', options);
  assert.equal(html, '<ul><li>a<ul><li>a1<ul><li>a1x</li></ul></li><li>a2</li></ul></li><li>b\ncontinued</li></ul><ol start="3"><li>three</li><li>four</li></ol>');
});

test('tables keep alignment as classes, escaped pipes and inline formatting', async () => {
  const {renderMarkdown} = await load();
  const html = renderMarkdown('| 名前 | 値 | 中 |\n|:---|---:|:-:|\n| **A** \\| x | 1 | `a|b` |', options);
  assert.match(html, /<th class="md-align-left">|<th>名前<\/th>/);
  assert.match(html, /<th class="md-align-right">値<\/th><th class="md-align-center">中<\/th>/);
  assert.match(html, /<td><strong>A<\/strong> \| x<\/td><td class="md-align-right">1<\/td><td class="md-align-center"><code>a\|b<\/code><\/td>/);
  assert.doesNotMatch(html, /style=/);
});

test('resolvePath never climbs above the repository root', async () => {
  const {resolvePath} = await load();
  assert.equal(resolvePath('research/a/b.md', './c/../d.md'), 'research/a/d.md');
  assert.equal(resolvePath('research/a/b.md', '../../README.md'), 'README.md');
  assert.equal(resolvePath('research/a/b.md', '../../../x'), null);
});
