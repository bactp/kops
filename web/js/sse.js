// Server-Sent Events over fetch streaming (cookie credentials), plus a pure incremental parser.

export class SSEParser {
  constructor() { this.buf = ''; this.event = ''; this.data = []; }
  // feed(text) -> array of {event, data} (data is the raw string)
  feed(chunk) {
    this.buf += chunk;
    const out = [];
    let idx;
    while ((idx = this.buf.search(/\r\n|\n|\r/)) >= 0) {
      const m = this.buf.slice(idx).match(/^(\r\n|\n|\r)/)[0];
      if (m === '\r' && idx + 1 === this.buf.length) break; // maybe half of \r\n
      const line = this.buf.slice(0, idx);
      this.buf = this.buf.slice(idx + m.length);
      if (line === '') {
        if (this.data.length) out.push({ event: this.event || 'message', data: this.data.join('\n') });
        this.event = ''; this.data = [];
      } else if (line[0] === ':') {
        // comment / keep-alive
      } else {
        const c = line.indexOf(':');
        const field = c < 0 ? line : line.slice(0, c);
        let value = c < 0 ? '' : line.slice(c + 1);
        if (value[0] === ' ') value = value.slice(1);
        if (field === 'event') this.event = value;
        else if (field === 'data') this.data.push(value);
      }
    }
    return out;
  }
}

export function parseEvent(ev) {
  let data = null;
  try { data = JSON.parse(ev.data); } catch { data = null; }
  return { event: ev.event, data };
}

// Resolves when the stream ends; rejects on network/HTTP error. onEvent receives {event,data}.
export async function streamEvents(url, { fetchImpl, signal, onEvent, onOpen } = {}) {
  const doFetch = fetchImpl || ((...a) => globalThis.fetch(...a));
  const res = await doFetch(url, { headers: { Accept: 'text/event-stream' }, credentials: 'same-origin', signal });
  if (!res.ok || !res.body) { const e = new Error(`SSE HTTP ${res.status}`); e.status = res.status; throw e; }
  if (onOpen) onOpen();
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  const parser = new SSEParser();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    for (const ev of parser.feed(dec.decode(value, { stream: true }))) onEvent(parseEvent(ev));
  }
}
