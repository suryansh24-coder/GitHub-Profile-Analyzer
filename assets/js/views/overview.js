import { api } from '../api.js';
import { make } from '../ui.js';

let mounted = false;

export async function mount() {
    if (mounted) return;
    mounted = true;
    try {
        const [health, programs] = await Promise.all([api.health(), api.programs('')]);
        document.getElementById('overview-api-state').textContent = health.status === 'ok' ? 'Online' : 'Limited';
        document.getElementById('overview-program-count').textContent = String(programs.total ?? 0);
        document.getElementById('sidebar-status-dot').className = 'status-dot is-online';
        document.getElementById('sidebar-status-text').textContent = `API online · GitHub ${health.integrations?.github?.authenticated ? 'token' : 'public'}`;
    } catch (err) {
        document.getElementById('overview-api-state').textContent = 'Offline';
        document.getElementById('sidebar-status-dot').className = 'status-dot is-offline';
        document.getElementById('sidebar-status-text').textContent = 'Backend offline';
        const note = make('p', 'disclaimer', err.message);
        document.querySelector('#view-overview .hero-panel').appendChild(note);
    }
}
