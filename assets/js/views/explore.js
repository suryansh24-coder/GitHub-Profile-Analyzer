import { api } from '../api.js';
import { badges, card, clear, empty, error, exportButton, formatDate, formatNumber, link, loading, make } from '../ui.js';

let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    document.getElementById('explore-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const results = document.getElementById('explore-results');
        loading(results, 'Searching GitHub repositories…');
        const params = new URLSearchParams({
            q: document.getElementById('explore-query').value.trim(),
            language: document.getElementById('explore-language').value.trim(),
            category: document.getElementById('explore-category').value,
            minStars: document.getElementById('explore-min-stars').value || '0',
            sort: document.getElementById('explore-sort').value,
            perPage: '12',
        });
        try {
            const data = await api.searchRepos(params.toString());
            clear(results);
            if (!data.items?.length) {
                empty(results, 'No repositories matched these filters. Try broader keywords or a lower star threshold.');
                return;
            }
            results.appendChild(make('p', 'card-sub', `${formatNumber(data.totalCount)} results · showing ${data.items.length} · query: ${data.query}`));
            data.items.forEach((repo) => results.appendChild(renderRepo(repo, data.query)));
        } catch (err) {
            error(results, err.message);
        }
    });
}

function renderRepo(repo, query) {
    const { shell, body } = card(repo.fullName || repo.name || 'Repository', repo.description || 'No description provided.', `${formatNumber(repo.stars)} stars`);
    const tones = { active: 'success', moderate: 'warn', quiet: '' };
    body.appendChild(badges([
        { text: repo.language || 'language unknown', tone: 'accent' },
        { text: `activity: ${repo.activityLevel || 'unknown'}`, tone: tones[repo.activityLevel] || '' },
        { text: `${formatNumber(repo.forks)} forks` },
        { text: `${formatNumber(repo.openIssues)} open issues` },
        ...(repo.license ? [{ text: repo.license }] : []),
    ]));
    if (repo.topics?.length) {
        const topics = make('p', 'card-sub', `Topics: ${repo.topics.join(', ')}`);
        body.appendChild(topics);
    }
    body.appendChild(make('p', 'disclaimer', `Last push: ${formatDate(repo.pushedAt)} · Contribution opportunities detected from open issues. This is not an abandonment claim.`));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(link(repo.htmlUrl));
    const toRepo = make('button', 'button button-secondary button-sm', 'Open in Repository Lab');
    toRepo.type = 'button';
    toRepo.addEventListener('click', () => {
        const input = document.getElementById('repo-input');
        input.value = repo.fullName || '';
        document.querySelector('[data-view="repository"]').click();
    });
    actions.appendChild(toRepo);
    actions.appendChild(exportButton(results, { repository: repo, query }, `Repository search — ${repo.fullName}`));
    body.appendChild(actions);
    return shell;
}
