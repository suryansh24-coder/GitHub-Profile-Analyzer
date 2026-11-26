import { api } from '../api.js';
import { card, clear, error, loading, make } from '../ui.js';

let mounted = false;

export function mount() {
    if (mounted) return;
    mounted = true;
    loadStatus();
    document.getElementById('ai-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const output = document.getElementById('ai-output');
        loading(output, 'Generating guidance…');
        try {
            const data = await api.aiComplete({
                prompt: document.getElementById('ai-task').value + ': ' + document.getElementById('ai-prompt').value.trim(),
                context: 'GitHub contribution planning workspace',
                maxTokens: 400,
            });
            clear(output);
            const { shell, body } = card('Generated guidance', 'Review critically. AI output is not a fact source.', data.model || 'AI');
            body.appendChild(make('p', 'card-sub', data.text));
            output.appendChild(shell);
        } catch (err) {
            error(output, err.message);
        }
    });
}

async function loadStatus() {
    const statusBox = document.getElementById('ai-status');
    loading(statusBox, 'Checking AI status…');
    try {
        const data = await api.aiStatus();
        clear(statusBox);
        const { shell, body } = card('AI availability', data.message || '', data.enabled ? 'enabled' : 'disabled');
        body.appendChild(make('p', 'card-sub', data.enabled ? `Model: ${data.model}. Requests are proxied through the backend; no key is exposed to the browser.` : data.setup || 'Set OPENAI_API_KEY on the backend to enable AI tools.'));
        statusBox.appendChild(shell);
    } catch (err) {
        error(statusBox, err.message);
    }
}
