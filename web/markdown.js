// Small, safe Markdown renderer for research documents. See docs/design-system.md.
// All source text is HTML-escaped; raw HTML in Markdown is shown as text, never parsed.
// Supported: headings, paragraphs, bold/italic/strikethrough, inline code, fenced code,
// ordered/unordered (nested) lists, tables, links/images, blockquotes, horizontal rules.
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const SAFE_SCHEME = /^(?:https?:|mailto:)/i;
const ANY_SCHEME = /^[a-z][a-z0-9+.-]*:/i;
const LIST_ITEM = /^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$/;
const FENCE = /^\s{0,3}(`{3,}|~{3,})\s*([\w+-]*)/;
const HEADING = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/;
const RULE = /^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/;
const TABLE_SEPARATOR = /^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$/;

// Resolve `href` against the directory of the repo-relative file `base`.
// Returns a normalized repo-relative path, or null when it climbs above the repo root.
export function resolvePath(base, href) {
  const parts = String(base || '').split('/').slice(0, -1);
  for (const part of href.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') { if (!parts.length) return null; parts.pop(); } else parts.push(part);
  }
  return parts.join('/');
}

export function slugify(text) {
  return 'md-' + (String(text).toLowerCase().replace(/<[^>]*>/g, '').replace(/&[a-z#0-9]+;/g, '').replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '') || 'section');
}

/**
 * Render Markdown to an HTML string.
 * options.basePath     repo-relative path of the Markdown file (for relative links)
 * options.resolveLink  (repoPath, fragment) => in-app href (e.g. '#r/<id>/<n>') or null
 * options.fileUrl      (repoPath) => URL for files outside the catalog, or null for plain text
 */
export function renderMarkdown(source, options = {}) {
  const context = {basePath: options.basePath || '', resolveLink: options.resolveLink || (() => null), fileUrl: options.fileUrl || (() => null), ids: new Map()};
  const lines = String(source ?? '').replace(/\u0000/g, '').replace(/\r\n?/g, '\n').split('\n');
  return blocks(lines, context);
}

function blocks(lines, ctx) {
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    let match;
    if ((match = line.match(FENCE))) {
      const fence = match[1], body = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith(fence)) body.push(lines[i++]);
      i++;
      const language = match[2] ? ` data-language="${esc(match[2])}"` : '';
      out.push(`<pre class="md-code"${language}><code>${esc(body.join('\n'))}</code></pre>`);
      continue;
    }
    if ((match = line.match(HEADING))) {
      const level = match[1].length, html = inline(match[2], ctx);
      out.push(`<h${level} id="${uniqueId(slugify(html), ctx)}">${html}</h${level}>`);
      i++;
      continue;
    }
    if (RULE.test(line)) { out.push('<hr>'); i++; continue; }
    if (/^\s{0,3}>/.test(line)) {
      const quoted = [];
      while (i < lines.length && lines[i].trim() && /^\s{0,3}>/.test(lines[i])) quoted.push(lines[i++].replace(/^\s{0,3}>\s?/, ''));
      out.push(`<blockquote>${blocks(quoted, ctx)}</blockquote>`);
      continue;
    }
    if (line.includes('|') && i + 1 < lines.length && TABLE_SEPARATOR.test(lines[i + 1]) && lines[i + 1].includes('|')) {
      const rows = [line];
      i += 2;
      const separator = lines[i - 1];
      while (i < lines.length && lines[i].trim() && lines[i].includes('|')) rows.push(lines[i++]);
      out.push(table(rows, separator, ctx));
      continue;
    }
    if (LIST_ITEM.test(line)) {
      const items = [];
      while (i < lines.length) {
        const current = lines[i];
        if (LIST_ITEM.test(current)) { items.push(current); i++; continue; }
        // Indented continuation lines belong to the previous item; a blank line ends the list
        // unless the next line is another item.
        if (current.trim() && /^\s+/.test(current) && items.length) { items.push(current); i++; continue; }
        if (!current.trim() && i + 1 < lines.length && LIST_ITEM.test(lines[i + 1])) { i++; continue; }
        break;
      }
      out.push(list(items, ctx));
      continue;
    }
    const paragraph = [];
    while (i < lines.length && lines[i].trim() && !startsBlock(lines, i)) paragraph.push(lines[i++]);
    if (!paragraph.length) paragraph.push(lines[i++]);
    out.push(`<p>${paragraph.map((text, n) => inline(text.trim(), ctx) + (n < paragraph.length - 1 ? (/(\s{2,}|\\)$/.test(text) ? '<br>' : '\n') : '')).join('')}</p>`);
  }
  return out.join('\n');
}

function startsBlock(lines, i) {
  const line = lines[i];
  return FENCE.test(line) || HEADING.test(line) || RULE.test(line) || /^\s{0,3}>/.test(line) || LIST_ITEM.test(line)
    || (line.includes('|') && i + 1 < lines.length && TABLE_SEPARATOR.test(lines[i + 1]) && lines[i + 1].includes('|'));
}

function uniqueId(id, ctx) {
  const seen = ctx.ids.get(id) || 0;
  ctx.ids.set(id, seen + 1);
  return seen ? `${id}-${seen + 1}` : id;
}

function splitRow(row) {
  const cells = [];
  let cell = '', code = false;
  const text = row.trim().replace(/^\|/, '').replace(/(?<!\\)\|$/, '');
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '\\' && text[i + 1] === '|') { cell += '|'; i++; continue; }
    if (ch === '`') code = !code;
    if (ch === '|' && !code) { cells.push(cell.trim()); cell = ''; continue; }
    cell += ch;
  }
  cells.push(cell.trim());
  return cells;
}

function table(rows, separator, ctx) {
  const aligns = splitRow(separator).map(cell => cell.startsWith(':') && cell.endsWith(':') ? 'center' : cell.endsWith(':') ? 'right' : '');
  const cell = (tag, text, n) => `<${tag}${aligns[n] ? ` class="md-align-${aligns[n]}"` : ''}>${inline(text, ctx)}</${tag}>`;
  const head = splitRow(rows[0]);
  const body = rows.slice(1).map(row => {
    const cells = splitRow(row);
    return `<tr>${head.map((_, n) => cell('td', cells[n] ?? '', n)).join('')}</tr>`;
  }).join('');
  return `<div class="md-table-scroll" tabindex="0" role="region" aria-label="表"><table><thead><tr>${head.map((text, n) => cell('th', text, n)).join('')}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function list(lines, ctx) {
  // Flatten into entries (continuation lines join the previous item), then nest by indent.
  const entries = [];
  for (const line of lines) {
    const match = line.match(LIST_ITEM);
    if (match) entries.push({indent: match[1].replace(/\t/g, '    ').length, ordered: /\d/.test(match[2]), start: parseInt(match[2], 10), text: match[3]});
    else if (entries.length) entries.at(-1).text += '\n' + line.trim();
  }
  const parse = (index, base) => {
    const node = {ordered: entries[index].ordered, start: entries[index].start, items: []};
    while (index < entries.length) {
      const entry = entries[index];
      if (entry.indent < base) break;
      if (entry.indent >= base + 2 && node.items.length) {
        const [child, next] = parse(index, entry.indent);
        node.items.at(-1).lists.push(child);
        index = next;
        continue;
      }
      if (entry.ordered !== node.ordered && node.items.length) break;
      node.items.push({text: entry.text, lists: []});
      index++;
    }
    return [node, index];
  };
  const render = node => {
    const tag = node.ordered ? 'ol' : 'ul';
    const start = node.ordered && node.start > 1 ? ` start="${node.start}"` : '';
    return `<${tag}${start}>${node.items.map(item => `<li>${task(item.text, ctx)}${item.lists.map(render).join('')}</li>`).join('')}</${tag}>`;
  };
  const out = [];
  for (let index = 0; index < entries.length;) {
    const [node, next] = parse(index, entries[index].indent);
    out.push(render(node));
    index = next;
  }
  return out.join('');
}

function task(text, ctx) {
  const match = text.match(/^\[([ xX])\]\s+(.*)$/s);
  if (!match) return inline(text, ctx);
  return `<span class="md-task${match[1] === ' ' ? '' : ' md-task-done'}" aria-hidden="true">${match[1] === ' ' ? '☐' : '☑'}</span> ${inline(match[2], ctx)}`;
}

// Inline formatting. Code spans, links and URLs become placeholders before escaping so
// their contents are not re-formatted; emphasis is applied to the escaped text.
export function inline(text, ctx = {resolveLink: () => null, fileUrl: () => null, basePath: ''}) {
  const tokens = [];
  const hold = html => `\u0000${tokens.push(html) - 1}\u0000`;
  let source = String(text ?? '').replace(/\u0000/g, '');
  source = source.replace(/(`+)([\s\S]*?[^`])\1(?!`)/g, (_, __, code) => hold(`<code>${esc(code.trim())}</code>`));
  source = source.replace(/\\([\\`*_{}\[\]()#+\-.!|~<>])/g, (_, ch) => hold(esc(ch)));
  source = source.replace(/(!?)\[((?:[^\[\]\u0000]|\[[^\[\]]*\])*)\]\(\s*<?([^\s()<>]*(?:\([^\s()]*\)[^\s()<>]*)*)>?(?:\s+(?:"([^"]*)"|'([^']*)'))?\s*\)/g,
    (_, bang, label, href, titleA, titleB) => hold(bang ? image(label, href, ctx) : link(inline(label, ctx), href, titleA ?? titleB, ctx)));
  source = source.replace(/<(https?:\/\/[^\s<>]+)>/g, (_, url) => hold(link(esc(url), url, null, ctx)));
  source = source.replace(/https?:\/\/[^\s<>"'`\u0000（）「」『』、。，．]+[^\s<>"'`\u0000（）「」『』、。，．.,:;!?)\]]/g, url => hold(link(esc(url), url, null, ctx)));
  let html = esc(source);
  html = html.replace(/\*\*(?=\S)([\s\S]*?\S)\*\*/g, '<strong>$1</strong>').replace(/(^|[^\w])__(?=\S)([\s\S]*?\S)__(?![\w])/g, '$1<strong>$2</strong>');
  html = html.replace(/(^|[^*])\*(?=[^\s*])([^*]*?[^\s*])\*(?!\*)/g, '$1<em>$2</em>').replace(/(^|[^\w])_(?=\S)([^_]*?\S)_(?![\w])/g, '$1<em>$2</em>');
  html = html.replace(/~~(?=\S)([\s\S]*?\S)~~/g, '<del>$1</del>');
  return html.replace(/\u0000(\d+)\u0000/g, (_, n) => tokens[Number(n)]).replace(/\u0000(\d+)\u0000/g, (_, n) => tokens[Number(n)]);
}

// Classify a link target. Returns {href, external, anchor} or null when it must not be a link.
export function linkTarget(href, ctx) {
  const raw = String(href ?? '').trim();
  if (!raw) return null;
  if (raw.startsWith('#')) return {href: '#', anchor: slugify(decodeURIComponentSafe(raw.slice(1)))};
  if (SAFE_SCHEME.test(raw)) return {href: raw, external: !/^mailto:/i.test(raw)};
  if (ANY_SCHEME.test(raw) || raw.startsWith('//')) return null;
  const [pathPart, fragment = ''] = raw.split('#');
  const path = resolvePath(ctx.basePath, decodeURIComponentSafe(pathPart.split('?')[0]));
  if (path === null) return null;
  const route = ctx.resolveLink(path, fragment);
  if (route) return {href: route};
  const url = ctx.fileUrl(path);
  return url ? {href: url, external: true} : null;
}

function decodeURIComponentSafe(value) {
  try { return decodeURIComponent(value); } catch { return value; }
}

function link(labelHtml, href, title, ctx) {
  const target = linkTarget(href, ctx);
  if (!target) return `<span class="md-link-disabled">${labelHtml}</span>`;
  const titleAttr = title ? ` title="${esc(title)}"` : '';
  if (target.anchor) return `<a href="#" data-doc-anchor="${esc(target.anchor)}"${titleAttr}>${labelHtml}</a>`;
  const external = target.external ? ' target="_blank" rel="noreferrer"' : '';
  return `<a href="${esc(target.href)}"${external}${titleAttr}>${labelHtml}${target.external && /^https?:/i.test(target.href) ? '<span class="md-external" aria-hidden="true">↗</span>' : ''}</a>`;
}

function image(alt, href, ctx) {
  const raw = String(href ?? '').trim();
  if (!raw || ANY_SCHEME.test(raw) || raw.startsWith('//')) return SAFE_SCHEME.test(raw) ? link(esc(alt || raw), raw, null, ctx) : esc(alt);
  const path = resolvePath(ctx.basePath, decodeURIComponentSafe(raw.split('#')[0]));
  const url = path === null ? null : ctx.fileUrl(path);
  return url ? `<img src="${esc(url)}" alt="${esc(alt)}" loading="lazy">` : esc(alt);
}
