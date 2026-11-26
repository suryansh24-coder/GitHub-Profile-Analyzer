const API_BASE = location.protocol === 'file:'
    ? 'http://127.0.0.1:8000/api'
    : '/api';

export async function request(path, options = {}) {
    let response;
    try {
        response = await fetch(`${API_BASE}${path}`, {
            headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) },
            ...options,
            body: options.body ? JSON.stringify(options.body) : undefined,
        });
    } catch (_) {
        throw new Error('Backend is unreachable. Start it with: uvicorn app.main:app --reload');
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const message = data?.error?.message || data?.detail || `Request failed with status ${response.status}`;
        throw new Error(Array.isArray(message) ? message.map((item) => item.msg || String(item)).join('; ') : String(message));
    }
    return data;
}

export const api = {
    health: () => request('/health'),
    programs: (params) => request(`/programs${params}`),
    profile: (username) => request(`/profile/${encodeURIComponent(username)}`),
    searchRepos: (params) => request(`/repos/search${params}`),
    matchIssues: (body) => request('/issues/match', { method: 'POST', body }),
    aiStatus: () => request('/ai/status'),
    aiComplete: (body) => request('/ai/complete', { method: 'POST', body }),
    repository: (tool, body) => request(`/repository/${tool}`, { method: 'POST', body }),
    export: (body) => request('/reports/export', { method: 'POST', body }),
};

export async function downloadReport(payload, title, format = 'markdown') {
    const result = await api.export({ format, title, payload });
    const blob = new Blob([result.content], { type: result.contentType || 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = result.filename || `${title}.${format}`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
