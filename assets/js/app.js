import * as ai from './views/ai.js';
import * as collab from './views/collab.js';
import * as contributions from './views/contributions.js';
import * as developer from './views/developer.js';
import * as explore from './views/explore.js';
import * as overview from './views/overview.js';
import * as programs from './views/programs.js';
import * as repository from './views/repository.js';

const modules = { overview, explore, contributions, programs, developer, repository, ai, collab, analyzer: {} };
const labels = {
    overview: 'Overview',
    explore: 'Open Source Explorer',
    contributions: 'Contribution Matcher',
    programs: 'Open Source Programs',
    developer: 'Developer DNA & Roadmap',
    repository: 'Repository Lab',
    ai: 'AI Developer Lab',
    collab: 'Collab Hub',
    analyzer: 'Profile Analyzer',
};

let active = 'overview';

function navigate(name, updateHash = true) {
    const view = modules[name] ? name : 'overview';
    active = view;
    document.querySelectorAll('.view').forEach((section) => section.classList.toggle('is-active', section.id === `view-${view}`));
    document.querySelectorAll('.nav-item').forEach((button) => button.classList.toggle('is-active', button.dataset.view === view));
    document.getElementById('current-view-label').textContent = labels[view];
    document.getElementById('platform-shell').classList.remove('nav-open');
    modules[view]?.mount?.();
    if (view === 'analyzer') requestAnimationFrame(() => requestAnimationFrame(resizeCharts));
    if (updateHash && location.hash !== `#${view}`) history.replaceState(null, '', `#${view}`);
    window.scrollTo({ top: 0, behavior: 'instant' in document.documentElement.style ? 'instant' : 'auto' });
}

function resizeCharts() {
    if (!window.Chart?.instances) return;
    Object.values(window.Chart.instances).forEach((chart) => chart.resize());
}

document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-view]');
    if (trigger) {
        event.preventDefault();
        navigate(trigger.dataset.view);
        return;
    }
    const link = event.target.closest('[data-view-link]');
    if (link) {
        event.preventDefault();
        navigate(link.dataset.viewLink);
    }
});

document.getElementById('menu-toggle').addEventListener('click', () => {
    document.getElementById('platform-shell').classList.toggle('nav-open');
});

window.addEventListener('hashchange', () => navigate(location.hash.slice(1), false));
navigate(location.hash.slice(1) || 'overview', false);
