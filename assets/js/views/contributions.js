import { api } from '../api.js';
import { badges, card, clear, empty, error, exportButton, link, loading, make } from '../ui.js';

let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    document.getElementById('match-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const results = document.getElementById('match-results');
        loading(results, 'Building skill map, searching issues and revalidating each candidate…');
        try {
            const data = await api.matchIssues({
                username: document.getElementById('match-username').value.trim(),
                query: document.getElementById('match-languages').value.trim(),
                limit: Number(document.getElementById('match-limit').value) || 8,
            });
            clear(results);
            if (!data.matches?.length) {
                empty(results, `No currently open matching issues found. Checked ${data.totalIssueCandidates ?? 0} candidates; ${data.skippedCount ?? 0} were closed, assigned or invalid.`);
                return;
            }
            results.appendChild(make('p', 'card-sub', `Skills used: ${data.skillSummary.map((item) => `${item.name} (${item.level})`).join(', ') || 'language evidence only'} · ${data.revalidatedCount} issues revalidated`));
            data.matches.forEach((match) => results.appendChild(renderMatch(match)));
            results.appendChild(make('p', 'disclaimer', data.disclaimer));
        } catch (err) {
            error(results, err.message);
        }
    });
}

function renderMatch(match) {
    const { shell, body } = card(match.title || 'Issue', match.repository || '', `match ${match.matchScore ?? 0}`);
    body.appendChild(badges([
        { text: `${match.difficulty || 'unknown'} complexity`, tone: match.difficulty === 'beginner' ? 'success' : '' },
        { text: `issue #${match.issueNumber ?? '—'}` },
        { text: match.language || 'language unknown', tone: 'accent' },
        ...(match.labels || []).map((label) => ({ text: label, tone: 'accent' })),
    ]));
    if (match.whyRecommended?.length) body.appendChild(make('p', 'reason', match.whyRecommended.join(' ')));
    if (match.startingGuide?.length) body.appendChild(make('p', 'card-sub', `Starting guide: ${match.startingGuide.join(' ')}`));
    body.appendChild(make('p', 'disclaimer', match.disclaimer));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(link(match.url, 'View open issue'));
    actions.appendChild(exportButton(results, { issue: match }, `Contribution match — ${match.title}`));
    body.appendChild(actions);
    return shell;
}
