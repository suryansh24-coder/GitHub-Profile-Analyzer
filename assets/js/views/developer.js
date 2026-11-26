import { api } from '../api.js';
import { badges, card, clear, empty, error, exportButton, formatDate, formatNumber, link, loading, make, meter } from '../ui.js';

let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    document.getElementById('developer-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const results = document.getElementById('developer-results');
        loading(results, 'Building developer intelligence from public GitHub data…');
        try {
            const data = await api.profile(document.getElementById('developer-username').value.trim());
            clear(results);
            results.appendChild(renderScores(data));
            results.appendChild(renderSkills(data));
            results.appendChild(renderTimeline(data));
            results.appendChild(renderStats(data));
            results.appendChild(make('p', 'disclaimer', data.limitations));
        } catch (err) {
            error(results, err.message);
        }
    });
}

function renderScores(data) {
    const { shell, body } = card(`Developer intelligence — @${data.profile.login}`, data.profile.bio || 'No public bio.', `${data.scores.legacy.score}/100 legacy`);
    const grid = make('div', 'score-grid');
    ['activity', 'portfolio', 'diversity', 'openSource', 'career'].forEach((key) => {
        const block = data.scores[key];
        const tile = make('div', 'score-tile');
        tile.appendChild(make('strong', '', block.score));
        tile.appendChild(make('span', '', block.name.replace(' Score', '')));
        tile.appendChild(meter(block.score));
        grid.appendChild(tile);
    });
    body.appendChild(grid);
    body.appendChild(make('p', 'disclaimer', data.scores.career.caveat));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(link(data.profile.htmlUrl, 'GitHub profile'));
    actions.appendChild(exportButton(document.getElementById('developer-results'), data, `Developer intelligence — ${data.profile.login}`));
    body.appendChild(actions);
    return shell;
}

function renderSkills(data) {
    const { shell, body } = card('Skill map', data.developerDna.note, `${data.developerDna.skills.length} skills`);
    const grid = make('div', 'card-body');
    data.developerDna.skills.forEach((skill) => {
        const item = make('div', 'list-item');
        item.appendChild(make('strong', '', `${skill.name} · ${skill.level}`));
        item.appendChild(make('div', 'card-sub', `Evidence in ${skill.evidenceCount} repository/repositories: ${skill.evidence.join(', ') || 'metadata only'}`));
        grid.appendChild(item);
    });
    if (data.developerDna.domains.length) {
        grid.appendChild(make('p', 'card-sub', `Domains: ${data.developerDna.domains.map((domain) => `${domain.name} (${domain.repositoryCount})`).join(', ')}`));
    }
    body.appendChild(grid);
    return shell;
}

function renderTimeline(data) {
    const { shell, body } = card('Roadmap from public history', 'Repository creation years and first observed technology use. No future events are invented.', `${data.growthTimeline.repositoriesPerYear.length} years`);
    const list = make('div', 'list');
    data.growthTimeline.repositoriesPerYear.forEach((entry) => {
        const item = make('div', 'list-item', `${entry.year}: ${entry.count} public ${entry.count === 1 ? 'repository' : 'repositories'}`);
        list.appendChild(item);
    });
    if (!data.growthTimeline.repositoriesPerYear.length) empty(list, 'No dated public repositories were returned.');
    body.appendChild(list);
    if (data.growthTimeline.technologyAdoption.length) {
        body.appendChild(make('p', 'card-sub', `First observed use: ${data.growthTimeline.technologyAdoption.map((entry) => `${entry.technology} (${entry.firstYear})`).join(', ')}`));
    }
    return shell;
}

function renderStats(data) {
    const { shell, body } = card('Portfolio snapshot', data.languageDataNote, formatNumber(data.statistics.totalStars));
    body.appendChild(badges([
        { text: `${formatNumber(data.statistics.totalRepos)} repositories`, tone: 'accent' },
        { text: `${formatNumber(data.statistics.originalRepos)} original` },
        { text: `${formatNumber(data.statistics.forkedRepos)} forks` },
        { text: `${formatNumber(data.profile.followers)} followers` },
        { text: `joined ${formatDate(data.profile.createdAt)}` },
    ]));
    body.appendChild(make('p', 'card-sub', `Most starred: ${data.statistics.mostStarred || 'none'} · Most recent: ${data.statistics.mostRecent || 'none'}`));
    const languages = make('div', 'list');
    Object.entries(data.languages).slice(0, 10).forEach(([language, bytes]) => {
        languages.appendChild(make('div', 'list-item', `${language}: ${formatNumber(bytes)} ${data.languageDataNote.startsWith('Byte') ? 'bytes' : 'repos'}`));
    });
    body.appendChild(languages);
    return shell;
}
