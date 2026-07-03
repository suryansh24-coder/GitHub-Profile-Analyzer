const API_BASE_URL = 'https://api.github.com';
let langChartInstance = null;
let repoChartInstance = null;

const themeToggleBtn = document.getElementById('theme-toggle');
const themeIconLight = document.getElementById('theme-icon-light');
const themeIconDark = document.getElementById('theme-icon-dark');

const searchForm = document.getElementById('search-form');
const githubInput = document.getElementById('github-input');
const errorMessage = document.getElementById('error-message');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('empty-state');
const dashboard = document.getElementById('dashboard');

const avatar = document.getElementById('avatar');
const nameEl = document.getElementById('name');
const usernameEl = document.getElementById('username');
const bioEl = document.getElementById('bio');
const followersEl = document.getElementById('followers');
const followingEl = document.getElementById('following');
const publicReposEl = document.getElementById('public-repos');
const joinedDateEl = document.getElementById('joined-date');

const totalReposStat = document.getElementById('total-repos-stat');
const totalStarsStat = document.getElementById('total-stars-stat');
const totalForksStat = document.getElementById('total-forks-stat');
const mostStarredStat = document.getElementById('most-starred-stat');
const recentRepoStat = document.getElementById('recent-repo-stat');

const scoreValueEl = document.getElementById('score-value');
const scoreLabelEl = document.getElementById('score-label');
const repoTableBody = document.getElementById('repo-table-body');

// Theme Management
const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
let currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
        themeIconLight.classList.add('hidden');
        themeIconDark.classList.remove('hidden');
        Chart.defaults.color = '#8b949e';
        Chart.defaults.borderColor = '#30363d';
    } else {
        themeIconDark.classList.add('hidden');
        themeIconLight.classList.remove('hidden');
        Chart.defaults.color = '#57606a';
        Chart.defaults.borderColor = '#d0d7de';
    }

    if (langChartInstance) langChartInstance.update();
    if (repoChartInstance) repoChartInstance.update();
}

applyTheme(currentTheme);

themeToggleBtn.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', currentTheme);
    applyTheme(currentTheme);
});

searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const inputVal = githubInput.value.trim();
    if (!inputVal) return;

    let username = inputVal;
    try {
        if (inputVal.includes('github.com')) {
            const url = new URL(inputVal.startsWith('http') ? inputVal : `https://${inputVal}`);
            const parts = url.pathname.split('/').filter(Boolean);
            if (parts.length > 0) username = parts[0];
        }
    } catch (err) {
        username = inputVal.replace(/^@/, '');
    }

    await analyzeProfile(username);
});

async function analyzeProfile(username) {
    hideError();
    showLoading();

    try {
        const userRes = await fetch(`${API_BASE_URL}/users/${username}`);
        if (!userRes.ok) {
            if (userRes.status === 404) throw new Error('User not found.');
            if (userRes.status === 403) throw new Error('API Rate limit exceeded. Try again later.');
            throw new Error('Failed to fetch user data.');
        }
        const userData = await userRes.json();

        const reposRes = await fetch(`${API_BASE_URL}/users/${username}/repos?per_page=100&sort=updated`);
        if (!reposRes.ok) throw new Error('Failed to fetch repositories.');
        let reposData = await reposRes.json();

        const stats = calculateRepoStats(reposData);

        // Fetch languages for top 10 repos by stars
        let languageUsage = {};
        const topReposForLanguages = [...reposData]
            .filter(r => !r.fork)
            .sort((a, b) => b.stargazers_count - a.stargazers_count)
            .slice(0, 10);

        await Promise.all(
            topReposForLanguages.map(async (repo) => {
                try {
                    const langRes = await fetch(`${API_BASE_URL}/repos/${username}/${repo.name}/languages`);
                    if (langRes.ok) {
                        const langData = await langRes.json();
                        for (const [lang, bytes] of Object.entries(langData)) {
                            languageUsage[lang] = (languageUsage[lang] || 0) + bytes;
                        }
                    }
                } catch (err) { }
            })
        );

        // Fallback
        if (Object.keys(languageUsage).length === 0) {
            reposData.forEach(repo => {
                if (repo.language) {
                    languageUsage[repo.language] = (languageUsage[repo.language] || 0) + 1;
                }
            });
        }

        const score = (stats.totalStars * 2) + (userData.public_repos * 3) + (userData.followers * 1);
        let scoreLabel = 'Beginner';
        let scoreClass = 'beginner';

        if (score >= 500) { scoreLabel = 'Elite Developer'; scoreClass = 'elite'; }
        else if (score >= 150) { scoreLabel = 'Advanced'; scoreClass = 'advanced'; }
        else if (score >= 50) { scoreLabel = 'Intermediate'; scoreClass = 'intermediate'; }

        updateProfileUI(userData);
        updateStatsUI(stats);
        updateScoreUI(score, scoreLabel, scoreClass);
        updateTable(reposData);

        renderLanguageChart(languageUsage);
        renderRepoChart(reposData);

        hideLoading();
        showDashboard();

    } catch (err) {
        hideLoading();
        showError(err.message);
    }
}

function calculateRepoStats(repos) {
    let totalStars = 0, totalForks = 0, mostStarred = null, mostRecent = null;
    repos.forEach(repo => {
        totalStars += repo.stargazers_count;
        totalForks += repo.forks_count;
        if (!mostStarred || repo.stargazers_count > mostStarred.stargazers_count) mostStarred = repo;
        if (!mostRecent || new Date(repo.updated_at) > new Date(mostRecent.updated_at)) mostRecent = repo;
    });
    return {
        totalRepos: repos.length,
        totalStars,
        totalForks,
        mostStarred: mostStarred ? mostStarred.name : 'N/A',
        mostRecent: mostRecent ? mostRecent.name : 'N/A'
    };
}

function updateProfileUI(user) {
    avatar.src = user.avatar_url;
    nameEl.textContent = user.name || user.login;
    usernameEl.textContent = `@${user.login}`;
    usernameEl.href = user.html_url;
    bioEl.textContent = user.bio || 'No bio available.';
    followersEl.textContent = formatNumber(user.followers);
    followingEl.textContent = formatNumber(user.following);
    publicReposEl.textContent = formatNumber(user.public_repos);
    const d = new Date(user.created_at);
    joinedDateEl.textContent = d.toLocaleDateString();
}

function updateStatsUI(stats) {
    totalReposStat.textContent = formatNumber(stats.totalRepos);
    totalStarsStat.textContent = formatNumber(stats.totalStars);
    totalForksStat.textContent = formatNumber(stats.totalForks);
    mostStarredStat.textContent = stats.mostStarred;
    recentRepoStat.textContent = stats.mostRecent;
}

function updateScoreUI(score, label, scoreClass) {
    // Animate score
    const finalScore = score;
    let currentScore = 0;
    const interval = setInterval(() => {
        currentScore += Math.ceil(finalScore / 20) || 1;
        if (currentScore >= finalScore) {
            currentScore = finalScore;
            clearInterval(interval);
        }
        scoreValueEl.textContent = currentScore;
    }, 40);

    scoreLabelEl.textContent = label;
    scoreLabelEl.className = `badge ${scoreClass}`;
}

function updateTable(repos) {
    repoTableBody.innerHTML = '';
    const sortedRepos = [...repos].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 10);
    if (sortedRepos.length === 0) {
        repoTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No repositories.</td></tr>';
        return;
    }
    sortedRepos.forEach(repo => {
        const tr = document.createElement('tr');
        const langHtml = repo.language ? `<span>${repo.language}</span>` : '<span style="color:#888">N/A</span>';
        const updatedD = new Date(repo.updated_at).toLocaleDateString();
        tr.innerHTML = `
            <td><a href="${repo.html_url}" target="_blank">${repo.name}</a></td>
            <td>${repo.stargazers_count}</td>
            <td>${repo.forks_count}</td>
            <td>${langHtml}</td>
            <td>${updatedD}</td>
        `;
        repoTableBody.appendChild(tr);
    });
}

function renderLanguageChart(langData) {
    const ctx = document.getElementById('languageChart').getContext('2d');
    if (langChartInstance) langChartInstance.destroy();
    const labels = Object.keys(langData);
    const data = Object.values(langData);
    if (labels.length === 0) { labels.push('Unknown'); data.push(1); }
    const bgColors = ['#0969da', '#2da44e', '#8250df', '#bf8700', '#cf222e', '#1f883d', '#ff7b72', '#a371f7'];
    langChartInstance = new Chart(ctx, {
        type: 'pie',
        data: { labels, datasets: [{ data, backgroundColor: bgColors }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
    });
}

function renderRepoChart(repos) {
    const ctx = document.getElementById('repoChart').getContext('2d');
    if (repoChartInstance) repoChartInstance.destroy();
    const topRepos = [...repos]
        .filter(r => r.stargazers_count > 0)
        .sort((a, b) => b.stargazers_count - a.stargazers_count)
        .slice(0, 8);
    const labels = topRepos.map(r => r.name.length > 15 ? r.name.substring(0, 15) + '...' : r.name);
    const data = topRepos.map(r => r.stargazers_count);
    if (labels.length === 0) { labels.push('No starred repos'); data.push(0); }
    repoChartInstance = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Stars', data, backgroundColor: '#0969da', borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function showLoading() {
    emptyState.classList.add('hidden');
    dashboard.classList.add('hidden');
    loading.classList.remove('hidden');
}
function hideLoading() { loading.classList.add('hidden'); }
function showError(msg) {
    errorMessage.textContent = msg;
    errorMessage.classList.remove('hidden');
    emptyState.classList.remove('hidden');
    dashboard.classList.add('hidden');
}
function hideError() { errorMessage.classList.add('hidden'); }
function showDashboard() { dashboard.classList.remove('hidden'); }
