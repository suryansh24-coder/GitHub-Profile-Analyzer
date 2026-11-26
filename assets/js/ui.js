export function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
}

export function make(tag, className = '', text = '') {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== '') element.textContent = String(text);
    return element;
}

export function loading(container, text = 'Working…') {
    clear(container).appendChild(make('div', 'loading-note', text));
}

export function error(container, message) {
    clear(container).appendChild(make('div', 'error-note', message));
}

export function empty(container, message) {
    clear(container).appendChild(make('p', 'empty-note', message));
}

export function card(title, subtitle = '', meta = '') {
    const shell = make('article', 'card');
    const head = make('div', 'card-head');
    const copy = make('div');
    copy.appendChild(make('h3', 'card-title', title));
    if (subtitle) copy.appendChild(make('p', 'card-sub', subtitle));
    head.appendChild(copy);
    if (meta) head.appendChild(make('span', 'card-meta', meta));
    shell.appendChild(head);
    const body = make('div', 'card-body');
    shell.appendChild(body);
    return { shell, body };
}

export function badge(text, tone = '') {
    return make('span', `tag${tone ? ` tag-${tone}` : ''}`, text);
}

export function badges(items) {
    const row = make('div', 'tag-row');
    items.forEach((item) => row.appendChild(typeof item === 'string' ? badge(item) : badge(item.text, item.tone)));
    return row;
}

export function formatNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return '—';
    if (number >= 1000000) return `${(number / 1000000).toFixed(1)}m`;
    if (number >= 1000) return `${(number / 1000).toFixed(1)}k`;
    return String(number);
}

export function formatDate(value) {
    if (!value) return 'not published';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function safeUrl(value) {
    try {
        const url = new URL(value);
        return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
    } catch (_) {
        return null;
    }
}

export function link(href, text = 'Open on GitHub') {
    const url = safeUrl(href);
    if (!url) return make('span', 'card-meta', 'Link unavailable');
    const anchor = make('a', 'link-button', text);
    anchor.href = url;
    anchor.target = '_blank';
    anchor.rel = 'noopener noreferrer';
    return anchor;
}

export function meter(value) {
    const wrap = make('div', 'meter');
    const fill = make('span');
    fill.style.width = `${Math.max(0, Math.min(100, Number(value) || 0))}%`;
    wrap.appendChild(fill);
    return wrap;
}

export function keyValues(pairs) {
    const list = make('dl', 'kv');
    pairs.forEach(([key, value]) => {
        list.appendChild(make('dt', '', key));
        list.appendChild(make('dd', '', value ?? '—'));
    });
    return list;
}

export function codeBlock(value) {
    return make('pre', 'code-block', typeof value === 'string' ? value : JSON.stringify(value, null, 2));
}

export function exportButton(container, payload, title) {
    const button = make('button', 'button button-secondary button-sm', 'Export Markdown');
    button.type = 'button';
    button.addEventListener('click', async () => {
        button.disabled = true;
        try {
            const { downloadReport } = await import('../api.js');
            await downloadReport(payload, title, 'markdown');
        } catch (err) {
            error(container, err.message);
        } finally {
            button.disabled = false;
        }
    });
    return button;
}
