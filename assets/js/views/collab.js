import { badge, card, clear, empty, error, link, make, safeUrl } from '../ui.js';

const STORAGE_KEY = 'devatlas.collab.entries';
let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    render();
    document.getElementById('collab-form').addEventListener('submit', (event) => {
        event.preventDefault();
        const title = document.getElementById('collab-title').value.trim();
        const url = document.getElementById('collab-url').value.trim();
        if (!safeUrl(url)) {
            error(document.getElementById('collab-results'), 'Enter a valid http or https URL.');
            return;
        }
        const entries = read();
        entries.unshift({ title, url, tags: document.getElementById('collab-tags').value.split(',').map((tag) => tag.trim()).filter(Boolean), savedAt: new Date().toISOString() });
        write(entries);
        event.target.reset();
        render();
    });
}

function read() {
    try {
        const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        return Array.isArray(value) ? value : [];
    } catch (_) {
        return [];
    }
}

function write(entries) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, 100)));
}

function render() {
    const container = document.getElementById('collab-results');
    clear(container);
    const entries = read();
    if (!entries.length) {
        empty(container, 'No saved entries yet. Add a repository, issue or program you find through the other views.');
        return;
    }
    entries.forEach((entry) => {
        const { shell, body } = card(entry.title, entry.url, new Date(entry.savedAt).toLocaleDateString());
        body.appendChild(link(entry.url, 'Open saved link'));
        if (entry.tags?.length) {
            const row = make('div', 'tool-buttons');
            entry.tags.forEach((tag) => row.appendChild(badge(tag)));
            body.appendChild(row);
        }
        const remove = make('button', 'button button-secondary button-sm', 'Remove');
        remove.type = 'button';
        remove.addEventListener('click', () => {
            write(read().filter((item) => item.url !== entry.url || item.title !== entry.title));
            render();
        });
        body.appendChild(remove);
        container.appendChild(shell);
    });
}
