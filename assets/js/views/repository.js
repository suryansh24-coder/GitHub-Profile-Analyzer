import { api } from '../api.js';
import { badge, badges, card, clear, codeBlock, empty, error, exportButton, loading, make } from '../ui.js';

let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    document.getElementById('repo-form').addEventListener('submit', (event) => {
        event.preventDefault();
        run('readme');
    });
    document.querySelectorAll('[data-repo-tool]').forEach((button) => {
        button.addEventListener('click', () => run(button.dataset.repoTool));
    });
}

async function run(tool) {
    const results = document.getElementById('repo-results');
    const repository = document.getElementById('repo-input').value.trim();
    if (!repository) {
        error(results, 'Enter a repository first.');
        return;
    }
    loading(results, `Running ${tool} against ${repository}…`);
    try {
        const data = await api.repository(endpointFor(tool), bodyFor(tool, repository));
        clear(results);
        results.appendChild(render(tool, data, results));
    } catch (err) {
        error(results, err.message);
    }
}

function endpointFor(tool) {
    return { readme: 'readme', health: 'health', xray: 'xray', 'pr-guard': 'pr-guard', docs: 'docs-generate' }[tool] || 'readme';
}

function bodyFor(tool, repository) {
    if (tool === 'pr-guard') {
        const raw = document.getElementById('repo-context').value.trim();
        const number = Number(raw.match(/\/pull\/(\d+)/)?.[1] || raw.replace(/\D/g, ''));
        if (!number) throw new Error('Enter a pull request number or pull request URL.');
        return { repository, number };
    }
    if (tool === 'xray') {
        return { repository, question: document.getElementById('repo-context').value.trim() || null };
    }
    if (tool === 'docs') {
        return { repository, kind: document.getElementById('repo-docs-kind').value };
    }
    return { repository };
}

function render(tool, data, container) {
    if (tool === 'readme') return renderReadme(data, container);
    if (tool === 'health') return renderHealth(data, container);
    if (tool === 'xray') return renderXray(data, container);
    if (tool === 'pr-guard') return renderPrGuard(data, container);
    return renderDocs(data);
}

function renderReadme(data, container) {
    const summary = Object.entries(data.analysis.summary || {}).map(([key, value]) => `${key}: ${value}`).join(' · ');
    const { shell, body } = card(`README Doctor — ${data.repository}`, summary, `grade ${data.analysis.grade || '—'} · ${data.analysis.score}/100`);
    body.appendChild(badges((data.analysis.findings || []).map((item) => ({ text: `${item.severity}: ${item.message}`, tone: ['high', 'critical'].includes(item.severity) ? 'danger' : 'warn' }))));
    body.appendChild(make('p', 'card-sub', `Original length: ${data.original.length} characters · Suggested length: ${data.suggested.length} characters`));
    const draft = make('details');
    draft.appendChild(make('summary', 'card-sub', 'Show improved README draft'));
    draft.appendChild(codeBlock(data.suggested));
    body.appendChild(draft);
    body.appendChild(make('p', 'disclaimer', data.warning));
    body.appendChild(make('p', 'disclaimer', data.writeAction.message));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(exportButton(container, data, `README Doctor — ${data.repository}`));
    body.appendChild(actions);
    return shell;
}

function renderHealth(data, container) {
    const result = data.health;
    const { shell, body } = card(`Repository health — ${data.repository}`, result.summary || '', `score ${result.score}/100`);
    const groups = ['documentation', 'legal', 'security', 'quality', 'activity'];
    groups.forEach((group) => {
        const items = (result.checks || []).filter((check) => check.category === group);
        if (!items.length) return;
        body.appendChild(make('h4', 'card-title', group));
        const list = make('div', 'list');
        items.forEach((check) => {
            const item = make('div', 'list-item');
            const tone = check.status === 'pass' ? 'success' : check.status === 'fail' ? 'danger' : 'warn';
            item.appendChild(badges([{ text: check.status, tone }, { text: check.severity }]));
            item.appendChild(make('div', 'card-sub', `${check.message} ${check.recommendation}`));
            list.appendChild(item);
        });
        body.appendChild(list);
    });
    if (result.dependencies) body.appendChild(codeBlock(result.dependencies));
    if (result.securityIntelligence) body.appendChild(make('p', 'disclaimer', `${result.securityIntelligence.secretScanning} · ${result.securityIntelligence.codeExecution}`));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(exportButton(container, data, `Repository health — ${data.repository}`));
    body.appendChild(actions);
    return shell;
}

function renderXray(data, container) {
    const { shell, body } = card(`Codebase X-Ray — ${data.repository}`, `${data.filesFetched} files analysed · ${data.treeTruncated ? 'tree truncated' : 'full tree read'}`, 'static analysis');
    const analysis = data.analysis;
    body.appendChild(badges([
        { text: `${analysis.statistics.filesAnalysed} files`, tone: 'accent' },
        { text: `${analysis.dependencyGraph.packageCount} packages` },
        { text: `${analysis.entrypoints.length} entrypoints` },
        { text: `${analysis.apiFlow.length} routes` },
    ]));
    body.appendChild(make('p', 'card-sub', (analysis.onboarding || []).join(' ')));
    body.appendChild(codeBlock({
        entrypoints: analysis.entrypoints,
        importantFiles: analysis.importantFiles,
        moduleRelationships: analysis.moduleRelationships,
        apiFlow: analysis.apiFlow,
        databaseModels: analysis.databaseModels,
        authentication: analysis.authentication,
        frontendBackendRelationship: analysis.frontendBackendRelationship,
        executionFlow: analysis.executionFlow,
        limitations: analysis.limitations,
    }));
    if (data.askResult?.hits?.length) {
        body.appendChild(make('h4', 'card-title', 'Evidence for your question'));
        data.askResult.hits.forEach((hit) => {
            body.appendChild(make('div', 'list-item', `${hit.path}:${hit.line} — ${hit.excerpt} (${hit.confidence})`));
        });
    }
    const actions = make('div', 'tool-buttons');
    actions.appendChild(exportButton(container, data, `Codebase X-Ray — ${data.repository}`));
    body.appendChild(actions);
    return shell;
}

function renderPrGuard(data, container) {
    const report = data.report;
    const { shell, body } = card(`PR Guardian — ${data.repository}`, (report.reviewerSummary || []).join(' '), `${report.changedFiles.length} files changed`);
    body.appendChild(make('h4', 'card-title', 'Confirmed findings'));
    const confirmed = make('div', 'list');
    (report.confirmedFindings || []).forEach((item) => {
        confirmed.appendChild(make('div', 'list-item', `${item.message} — ${item.evidence}`));
    });
    if (!report.confirmedFindings?.length) empty(confirmed, 'No confirmed findings from the returned metadata.');
    body.appendChild(confirmed);
    body.appendChild(make('h4', 'card-title', 'Hypotheses'));
    const hypotheses = make('div', 'list');
    (report.hypotheses || []).forEach((item) => {
        hypotheses.appendChild(make('div', 'list-item', `${item.message} — ${item.evidence}`));
    });
    if (!report.hypotheses?.length) empty(hypotheses, 'No hypotheses generated.');
    body.appendChild(hypotheses);
    if (report.testRecommendations?.length) body.appendChild(make('p', 'card-sub', `Test recommendations: ${report.testRecommendations.join('; ')}`));
    body.appendChild(make('p', 'disclaimer', report.limitations));
    const actions = make('div', 'tool-buttons');
    actions.appendChild(exportButton(container, data, `PR Guardian — ${data.repository}`));
    body.appendChild(actions);
    return shell;
}

function renderDocs(data) {
    const { shell, body } = card(`Draft: ${data.filename}`, data.repository, data.kind);
    body.appendChild(codeBlock(data.content));
    body.appendChild(make('p', 'disclaimer', data.warning));
    return shell;
}
