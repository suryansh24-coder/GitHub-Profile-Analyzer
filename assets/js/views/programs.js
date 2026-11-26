import { api } from '../api.js';
import { badges, card, clear, empty, error, formatDate, link, loading, make } from '../ui.js';

let mounted = false;
let timer;

export function mount() {
    if (mounted) return;
    mounted = true;
    document.getElementById('program-refresh').addEventListener('click', load);
    document.getElementById('program-filter-status').addEventListener('change', load);
    document.getElementById('program-beginner').addEventListener('change', load);
    document.getElementById('program-mentorship').addEventListener('change', load);
    document.getElementById('program-filter-search').addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(load, 250);
    });
    load();
}

async function load() {
    const results = document.getElementById('program-results');
    loading(results, 'Loading verified programs…');
    const params = new URLSearchParams();
    const search = document.getElementById('program-filter-search').value.trim();
    const status = document.getElementById('program-filter-status').value;
    if (search) params.set('search', search);
    if (status) params.set('status', status);
    if (document.getElementById('program-beginner').checked) params.set('beginnerFriendly', 'true');
    if (document.getElementById('program-mentorship').checked) params.set('mentorship', 'true');
    try {
        const data = await api.programs(params.toString());
        if (data.error) throw new Error(data.error.message);
        clear(results);
        if (!data.items?.length) {
            empty(results, 'No verified programs match these filters.');
            return;
        }
        data.items.forEach((program) => results.appendChild(renderProgram(program)));
        results.appendChild(make('p', 'disclaimer', data.verificationNote));
    } catch (err) {
        error(results, err.message);
    }
}

function renderProgram(program) {
    const { shell, body } = card(program.name, program.description || '', `verified ${formatDate(program.lastVerified)}`);
    const tones = { applications_open: 'success', upcoming: 'warn', ongoing: 'accent', applications_closed: 'danger', completed: '', status_unverified: 'warn' };
    body.appendChild(badges([
        { text: program.status || 'status unknown', tone: tones[program.status] || '' },
        { text: `deadline: ${program.applicationDeadline ? formatDate(program.applicationDeadline) : 'not published'}` },
        { text: program.organization || 'organization unknown' },
        ...(program.tags || []).slice(0, 5).map((tag) => ({ text: tag })),
    ]));
    body.appendChild(make('p', 'card-sub', program.eligibility || 'Eligibility details are available on the official site.'));
    if (program.duration) body.appendChild(make('p', 'disclaimer', `Duration or period: ${program.duration}`));
    if (program.notes) body.appendChild(make('p', 'disclaimer', program.notes));
    actions(body, program);
    return shell;
}

function actions(body, program) {
    const row = make('div', 'tool-buttons');
    row.appendChild(link(program.officialUrl, 'Official program page'));
    if (program.applicationUrl && program.applicationUrl !== program.officialUrl) row.appendChild(link(program.applicationUrl, 'Applications'));
    if (program.verificationSource) row.appendChild(link(program.verificationSource, 'Verification source'));
    body.appendChild(row);
}
