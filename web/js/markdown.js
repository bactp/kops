// Tiny safe markdown renderer. Every piece of input text is HTML-escaped before it is placed in output.
// Supports: headings, paragraphs, ordered/unordered lists, fenced code blocks, inline code, bold, italic, links.

export function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

export function safeUrl(u) {
  const t = String(u).trim();
  return /^(https?:\/\/|mailto:|#|\/(?!\/))/i.test(t) ? t : null;
}

function inline(text) {
  const codes = [];
  // pull inline code out first so its content is not further formatted
  let s = text.replace(/`([^`\n]+)`/g, (_, c) => { codes.push(c); return `\u0000${codes.length - 1}\u0000`; });
  s = escapeHtml(s);
  s = s.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, (m, label, url) => {
    // url was already escaped; unescape &amp; only for the scheme test, keep escaped output
    const raw = url.replace(/&amp;/g, '&');
    const ok = safeUrl(raw);
    return ok ? `<a href="${escapeHtml(ok)}" target="_blank" rel="noopener noreferrer">${label}</a>` : m;
  });
  s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*\w])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
  s = s.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${escapeHtml(codes[Number(i)])}</code>`);
  return s;
}

export function renderMarkdown(md) {
  const lines = String(md == null ? '' : md).replace(/\r\n?/g, '\n').split('\n');
  const out = [];
  let i = 0;
  let para = [];
  const flush = () => { if (para.length) { out.push(`<p>${inline(para.join(' '))}</p>`); para = []; } };
  while (i < lines.length) {
    const line = lines[i];
    const fence = line.match(/^\s*```+\s*([\w-]*)\s*$/);
    if (fence) {
      flush();
      const body = [];
      i++;
      while (i < lines.length && !/^\s*```+\s*$/.test(lines[i])) body.push(lines[i++]);
      i++; // closing fence (or EOF)
      out.push(`<pre><code>${escapeHtml(body.join('\n'))}</code></pre>`);
      continue;
    }
    const hd = line.match(/^(#{1,6})\s+(.*?)\s*#*\s*$/);
    if (hd) { flush(); const n = Math.min(6, hd[1].length + 1); out.push(`<h${n}>${inline(hd[2])}</h${n}>`); i++; continue; }
    const ul = line.match(/^\s*[-*+]\s+(.*)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ul || ol) {
      flush();
      const tag = ul ? 'ul' : 'ol';
      const re = ul ? /^\s*[-*+]\s+(.*)$/ : /^\s*\d+[.)]\s+(.*)$/;
      const items = [];
      while (i < lines.length) {
        const m = lines[i].match(re);
        if (m) { items.push(m[1]); i++; }
        else if (/^\s+\S/.test(lines[i]) && items.length) { items[items.length - 1] += ` ${lines[i].trim()}`; i++; }
        else break;
      }
      out.push(`<${tag}>${items.map((t) => `<li>${inline(t)}</li>`).join('')}</${tag}>`);
      continue;
    }
    if (line.trim() === '') { flush(); i++; continue; }
    para.push(line.trim());
    i++;
  }
  flush();
  return out.join('\n');
}
