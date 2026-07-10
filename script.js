/* ═══════════════════════════════════════════════════════════════════════
   GitHub Profile Analyzer — script.js
   Fixed productivity score (normalized 0–100) + deep analysis engine
   ═══════════════════════════════════════════════════════════════════════ */

const API_BASE_URL = 'https://api.github.com';
let langChartInstance = null;
let repoChartInstance = null;

// ── DOM refs ──────────────────────────────────────────────────────────────
const themeToggleBtn  = document.getElementById('theme-toggle');
const themeIconLight  = document.getElementById('theme-icon-light');
const themeIconDark   = document.getElementById('theme-icon-dark');
const searchForm      = document.getElementById('search-form');
const githubInput     = document.getElementById('github-input');
const errorMessage    = document.getElementById('error-message');
const loading         = document.getElementById('loading');
const emptyState      = document.getElementById('empty-state');
const dashboard       = document.getElementById('dashboard');

// Profile
const avatar        = document.getElementById('avatar');
const nameEl        = document.getElementById('name');
const usernameEl    = document.getElementById('username');
const bioEl         = document.getElementById('bio');
const followersEl   = document.getElementById('followers');
const followingEl   = document.getElementById('following');
const publicReposEl = document.getElementById('public-repos');
const joinedDateEl  = document.getElementById('joined-date');
const locationLine  = document.getElementById('location-line');
const locationVal   = document.getElementById('location-val');
const companyLine   = document.getElementById('company-line');
const companyVal    = document.getElementById('company-val');

// Stats
const totalReposStat    = document.getElementById('total-repos-stat');
const totalStarsStat    = document.getElementById('total-stars-stat');
const totalForksStat    = document.getElementById('total-forks-stat');
const originalReposStat = document.getElementById('original-repos-stat');
const forkedByYouStat   = document.getElementById('forked-by-you-stat');
const mostStarredStat   = document.getElementById('most-starred-stat');
const recentRepoStat    = document.getElementById('recent-repo-stat');

// Score
const scoreValueEl = document.getElementById('score-value');
const scoreLabelEl = document.getElementById('score-label');
const gaugeFill    = document.getElementById('gauge-fill');

// Score breakdown
const sStars     = document.getElementById('s-stars');
const sRepos     = document.getElementById('s-repos');
const sFollowers = document.getElementById('s-followers');
const sLangs     = document.getElementById('s-langs');
const sAge       = document.getElementById('s-age');

// Insight strip
const insAge       = document.getElementById('ins-age');
const insAvgStars  = document.getElementById('ins-avg-stars');
const insForkRatio = document.getElementById('ins-fork-ratio');
const insLangsCount= document.getElementById('ins-langs-count');

const repoTableBody = document.getElementById('repo-table-body');
const analysisGrid  = document.getElementById('analysis-grid');

// ── Theme ─────────────────────────────────────────────────────────────────
const savedTheme = localStorage.getItem('theme');
let currentTheme = savedTheme || 'dark';

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
        themeIconLight.classList.add('hidden');
        themeIconDark.classList.remove('hidden');
        Chart.defaults.color       = '#64748b';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    } else {
        themeIconDark.classList.add('hidden');
        themeIconLight.classList.remove('hidden');
        Chart.defaults.color       = '#64748b';
        Chart.defaults.borderColor = 'rgba(0,0,0,0.08)';
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

// ── Search ────────────────────────────────────────────────────────────────
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const inputVal = githubInput.value.trim();
    if (!inputVal) return;

    let username = inputVal.replace(/^@/, '');
    try {
        if (inputVal.includes('github.com')) {
            const url   = new URL(inputVal.startsWith('http') ? inputVal : `https://${inputVal}`);
            const parts = url.pathname.split('/').filter(Boolean);
            if (parts.length > 0) username = parts[0];
        }
    } catch (_) {
        username = inputVal.replace(/^@/, '');
    }

    await analyzeProfile(username);
});

// ── Main analysis ─────────────────────────────────────────────────────────
async function analyzeProfile(username) {
    hideError();
    showLoading();

    try {
        // ── Fetch user + repos ────────────────────────────────────────────
        const [userRes, reposRes] = await Promise.all([
            fetch(`${API_BASE_URL}/users/${username}`),
            fetch(`${API_BASE_URL}/users/${username}/repos?per_page=100&sort=updated`)
        ]);

        if (!userRes.ok) {
            if (userRes.status === 404) throw new Error('User not found. Check the username and try again.');
            if (userRes.status === 403) throw new Error('GitHub API rate limit exceeded. Please wait a minute and try again.');
            throw new Error('Failed to fetch user data.');
        }
        if (!reposRes.ok) throw new Error('Failed to fetch repositories.');

        const userData  = await userRes.json();
        const reposData = await reposRes.json();

        // ── Fetch languages for top repos ─────────────────────────────────
        let languageUsage = {};
        const topRepos = [...reposData]
            .filter(r => !r.fork)
            .sort((a, b) => b.stargazers_count - a.stargazers_count)
            .slice(0, 12);

        await Promise.all(topRepos.map(async (repo) => {
            try {
                const langRes = await fetch(`${API_BASE_URL}/repos/${username}/${repo.name}/languages`);
                if (langRes.ok) {
                    const langData = await langRes.json();
                    for (const [lang, bytes] of Object.entries(langData)) {
                        languageUsage[lang] = (languageUsage[lang] || 0) + bytes;
                    }
                }
            } catch (_) {}
        }));

        // Fallback to repo.language field
        if (Object.keys(languageUsage).length === 0) {
            reposData.forEach(repo => {
                if (repo.language) {
                    languageUsage[repo.language] = (languageUsage[repo.language] || 0) + 1;
                }
            });
        }

        // ── Compute everything ────────────────────────────────────────────
        const stats = calculateRepoStats(reposData);
        const { score, breakdown, tier, tierClass } = computeScore(userData, stats, languageUsage);
        const insights = computeInsights(userData, reposData, stats, languageUsage);

        // ── Render ────────────────────────────────────────────────────────
        updateProfileUI(userData);
        updateStatsUI(stats);
        updateInsightStrip(insights);
        updateScoreUI(score, breakdown, tier, tierClass);
        updateDeepAnalysis(insights, userData, stats, languageUsage);
        updateTable(reposData);
        renderLanguageChart(languageUsage);
        renderRepoChart(reposData);
        renderContributionHeatmap(userData.login);

        hideLoading();
        showDashboard();

    } catch (err) {
        hideLoading();
        showError(err.message);
    }
}

// ── Productivity Score (fixed, normalized 0–100) ──────────────────────────
/*
  Multi-dimensional scoring, each component capped and weighted:
  
  Component           Max raw    Weight   Max contribution
  ─────────────────── ────────   ──────   ────────────────
  Stars               1000       30pts    log-scaled
  Portfolio size      100 repos  25pts    log-scaled
  Community (followers) 5000    20pts    log-scaled
  Language diversity  10 langs   10pts    linear
  Account maturity    10 years   15pts    linear
  ────────────────────────────────────────────────────────
  Total                                  100 pts
*/
function computeScore(user, stats, langUsage) {
    const MAX_SCORE = 100;

    // Stars component (0–30): log scale, 1000+ stars → 30
    const starScore = Math.min(30, Math.round(30 * Math.log10(stats.totalStars + 1) / Math.log10(1001)));

    // Repos component (0–25): log scale, 100 repos → 25
    const repoScore = Math.min(25, Math.round(25 * Math.log10(user.public_repos + 1) / Math.log10(101)));

    // Followers component (0–20): log scale, 5000+ → 20
    const followerScore = Math.min(20, Math.round(20 * Math.log10(user.followers + 1) / Math.log10(5001)));

    // Language diversity (0–10): each unique lang = 1pt, cap 10
    const langCount = Object.keys(langUsage).length;
    const langScore = Math.min(10, langCount);

    // Account maturity (0–15): years since joined, cap 10 years
    const joinedDate  = new Date(user.created_at);
    const yearsActive = (Date.now() - joinedDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
    const ageScore    = Math.min(15, Math.round(15 * Math.min(yearsActive, 10) / 10));

    const total = starScore + repoScore + followerScore + langScore + ageScore;

    let tier = 'Beginner', tierClass = 'beginner';
    if (total >= 80)      { tier = '🏆 Elite Dev';     tierClass = 'elite'; }
    else if (total >= 60) { tier = '💜 Advanced';       tierClass = 'advanced'; }
    else if (total >= 35) { tier = '🔵 Intermediate';  tierClass = 'intermediate'; }

    return {
        score: total,
        breakdown: {
            stars:     starScore,
            repos:     repoScore,
            followers: followerScore,
            langs:     langScore,
            age:       ageScore
        },
        tier,
        tierClass
    };
}

// ── Compute insight data ──────────────────────────────────────────────────
function computeInsights(user, repos, stats, langUsage) {
    const joinedDate  = new Date(user.created_at);
    const yearsActive = ((Date.now() - joinedDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25)).toFixed(1);

    const originalRepos = repos.filter(r => !r.fork);
    const forkRepos     = repos.filter(r => r.fork);
    const avgStars      = originalRepos.length
        ? (stats.totalStars / originalRepos.length).toFixed(1)
        : '0';

    const topLang = Object.entries(langUsage)
        .sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

    const totalBytes = Object.values(langUsage).reduce((a, b) => a + b, 0);
    const topLangPct = totalBytes && Object.keys(langUsage).length
        ? Math.round((langUsage[topLang] / totalBytes) * 100)
        : 0;

    // Most active language diversity
    const langCount = Object.keys(langUsage).length;

    // Recent activity: repos updated in last 3 months
    const threeMonthsAgo = Date.now() - (90 * 24 * 60 * 60 * 1000);
    const recentlyActive  = repos.filter(r => new Date(r.updated_at).getTime() > threeMonthsAgo).length;

    // Average repo size
    const avgSize = repos.length
        ? Math.round(repos.reduce((a, r) => a + r.size, 0) / repos.length)
        : 0;

    // Has description on repos
    const withDesc = repos.filter(r => r.description).length;
    const descRatio = repos.length ? Math.round((withDesc / repos.length) * 100) : 0;

    // Watcher count (approximation of community interest)
    const totalWatchers = repos.reduce((a, r) => a + (r.watchers_count || 0), 0);

    // Open issues
    const totalIssues = repos.reduce((a, r) => a + r.open_issues_count, 0);

    // Topic usage
    const topicsUsed = repos.reduce((a, r) => a + (r.topics?.length || 0), 0);

    return {
        yearsActive,
        avgStars,
        forkCount: forkRepos.length,
        originalCount: originalRepos.length,
        forkRatioPct: repos.length ? Math.round((originalRepos.length / repos.length) * 100) : 100,
        langCount,
        topLang,
        topLangPct,
        recentlyActive,
        avgSize,
        descRatio,
        totalWatchers,
        totalIssues,
        topicsUsed
    };
}

// ── UI updates ────────────────────────────────────────────────────────────
function updateProfileUI(user) {
    avatar.src          = user.avatar_url;
    nameEl.textContent  = user.name || user.login;
    usernameEl.textContent = `@${user.login}`;
    usernameEl.href     = user.html_url;
    bioEl.textContent   = user.bio || 'No bio provided.';
    followersEl.textContent  = formatNumber(user.followers);
    followingEl.textContent  = formatNumber(user.following);
    publicReposEl.textContent= formatNumber(user.public_repos);
    const d = new Date(user.created_at);
    joinedDateEl.textContent = d.toLocaleDateString('en-GB', { day:'2-digit', month:'long', year:'numeric' });

    if (user.location) {
        locationVal.textContent = user.location;
        locationLine.style.display = 'block';
    } else { locationLine.style.display = 'none'; }

    if (user.company) {
        companyVal.textContent = user.company.replace(/^@/, '');
        companyLine.style.display = 'block';
    } else { companyLine.style.display = 'none'; }
}

function updateStatsUI(stats) {
    totalReposStat.textContent    = formatNumber(stats.totalRepos);
    totalStarsStat.textContent    = formatNumber(stats.totalStars);
    totalForksStat.textContent    = formatNumber(stats.totalForks);
    originalReposStat.textContent = formatNumber(stats.originalRepos);
    forkedByYouStat.textContent   = formatNumber(stats.forkedByUser);
    mostStarredStat.textContent   = stats.mostStarred;
    recentRepoStat.textContent    = stats.mostRecent;
}

function updateInsightStrip(ins) {
    insAge.textContent        = ins.yearsActive;
    insAvgStars.textContent   = ins.avgStars;
    insForkRatio.textContent  = ins.originalCount + ' / ' + (ins.originalCount + ins.forkCount);
    insLangsCount.textContent = ins.langCount;
}

function updateScoreUI(score, breakdown, tier, tierClass) {
    // Animate the numeric value
    let cur = 0;
    const step = Math.max(1, Math.ceil(score / 40));
    const interval = setInterval(() => {
        cur += step;
        if (cur >= score) { cur = score; clearInterval(interval); }
        scoreValueEl.textContent = cur;
    }, 35);

    // Animate the SVG gauge arc
    // Arc full = 306 (270° of circumference for r=65: 2π×65 × (270/360) ≈ 306)
    const ARC_LEN = 306;
    const filled  = (score / 100) * ARC_LEN;
    setTimeout(() => {
        gaugeFill.style.strokeDasharray = `${filled} 408`;
    }, 80);

    // Badge
    scoreLabelEl.textContent = tier;
    scoreLabelEl.className   = `badge ${tierClass}`;

    // Breakdown rows
    sStars.textContent     = breakdown.stars    + ' pts';
    sRepos.textContent     = breakdown.repos    + ' pts';
    sFollowers.textContent = breakdown.followers+ ' pts';
    sLangs.textContent     = breakdown.langs    + ' pts';
    sAge.textContent       = breakdown.age      + ' pts';
}

function updateDeepAnalysis(ins, user, stats, langUsage) {
    const items = [
        {
            icon: '📈',
            title: 'Account Maturity',
            desc: `Active for ${ins.yearsActive} years (since ${new Date(user.created_at).getFullYear()}).`,
            val: ins.yearsActive >= 5
                ? '✅ Established developer'
                : ins.yearsActive >= 2
                    ? '🔵 Growing profile'
                    : '🟡 Early-stage account'
        },
        {
            icon: '⭐',
            title: 'Star Performance',
            desc: `${formatNumber(stats.totalStars)} total stars across ${ins.originalCount} original repos — avg ${ins.avgStars} stars per repo.`,
            val: ins.avgStars >= 10
                ? '🔥 High-impact repos'
                : ins.avgStars >= 3
                    ? '📈 Gaining traction'
                    : '📦 Building portfolio'
        },
        {
            icon: '🧬',
            title: 'Language Specialization',
            desc: `Primary language is ${ins.topLang} (${ins.topLangPct}% of codebase). ${ins.langCount} total languages detected.`,
            val: ins.langCount >= 6
                ? '🌐 Polyglot developer'
                : ins.langCount >= 3
                    ? '🎯 Multi-stack capable'
                    : '🔧 Focused specialist'
        },
        {
            icon: '🔱',
            title: 'Portfolio Originality',
            desc: `${ins.originalCount} original projects vs ${ins.forkCount} forks (${ins.forkRatioPct}% original).`,
            val: ins.forkRatioPct >= 80
                ? '✨ Highly original'
                : ins.forkRatioPct >= 50
                    ? '⚖️ Mixed portfolio'
                    : '🍴 Fork-heavy'
        },
        {
            icon: '🕐',
            title: 'Recent Activity',
            desc: `${ins.recentlyActive} repositor${ins.recentlyActive === 1 ? 'y' : 'ies'} updated in the last 90 days.`,
            val: ins.recentlyActive >= 5
                ? '🔥 Very active'
                : ins.recentlyActive >= 2
                    ? '💡 Moderately active'
                    : '😴 Relatively quiet recently'
        },
        {
            icon: '👥',
            title: 'Community Reach',
            desc: `${formatNumber(user.followers)} followers, ${formatNumber(ins.totalWatchers)} total watchers across repos.`,
            val: user.followers >= 100
                ? '🌟 Strong community'
                : user.followers >= 20
                    ? '📣 Building audience'
                    : '🌱 Early community'
        },
        {
            icon: '📝',
            title: 'Documentation Habit',
            desc: `${ins.descRatio}% of repositories have descriptions. ${ins.topicsUsed} topics used overall.`,
            val: ins.descRatio >= 70
                ? '📚 Well documented'
                : ins.descRatio >= 40
                    ? '📄 Partially documented'
                    : '⚠️ Needs better docs'
        },
        {
            icon: '🐛',
            title: 'Open Issues',
            desc: `${formatNumber(ins.totalIssues)} open issues across all repos — reflects engagement & maintenance.`,
            val: ins.totalIssues >= 20
                ? '🔧 Actively maintained'
                : ins.totalIssues >= 5
                    ? '🔍 Moderate activity'
                    : '✅ Clean issue slate'
        }
    ];

    analysisGrid.innerHTML = items.map(item => `
        <div class="analysis-item">
            <span class="ai-icon">${item.icon}</span>
            <div class="ai-content">
                <span class="ai-title">${item.title}</span>
                <span class="ai-desc">${item.desc}</span>
                <span class="ai-val">${item.val}</span>
            </div>
        </div>
    `).join('');
}

function updateTable(repos) {
    repoTableBody.innerHTML = '';
    const sorted = [...repos].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 15);
    if (!sorted.length) {
        repoTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted)">No repositories found.</td></tr>';
        return;
    }
    sorted.forEach(repo => {
        const tr  = document.createElement('tr');
        const upd = new Date(repo.updated_at).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' });
        const langHtml = repo.language
            ? `<span class="lang-chip">${repo.language}</span>`
            : `<span style="color:var(--text-muted);font-size:0.8rem">—</span>`;
        tr.innerHTML = `
            <td><a href="${repo.html_url}" target="_blank" rel="noopener">${repo.name}${repo.fork ? ' <span style="font-size:0.72rem;opacity:0.6">(fork)</span>' : ''}</a></td>
            <td>${repo.stargazers_count}</td>
            <td>${repo.forks_count}</td>
            <td>${langHtml}</td>
            <td>${formatNumber(repo.size)}</td>
            <td>${upd}</td>
        `;
        repoTableBody.appendChild(tr);
    });
}

// ── Repo stats calculator ──────────────────────────────────────────────────
function calculateRepoStats(repos) {
    let totalStars = 0, totalForks = 0;
    let mostStarred = null, mostRecent = null;
    const originalRepos = repos.filter(r => !r.fork);
    const forkedByUser  = repos.filter(r =>  r.fork);

    repos.forEach(repo => {
        totalStars += repo.stargazers_count;
        totalForks += repo.forks_count;
        if (!mostStarred || repo.stargazers_count > mostStarred.stargazers_count) mostStarred = repo;
        if (!mostRecent  || new Date(repo.updated_at) > new Date(mostRecent.updated_at))   mostRecent  = repo;
    });

    return {
        totalRepos:    repos.length,
        totalStars,
        totalForks,
        originalRepos: originalRepos.length,
        forkedByUser:  forkedByUser.length,
        mostStarred:   mostStarred ? mostStarred.name : 'N/A',
        mostRecent:    mostRecent  ? mostRecent.name  : 'N/A'
    };
}

// ── Charts ────────────────────────────────────────────────────────────────
const CHART_COLORS = [
    '#7c3aed','#06b6d4','#f59e0b','#10b981',
    '#ef4444','#8b5cf6','#0ea5e9','#f97316',
    '#84cc16','#ec4899','#14b8a6','#a855f7'
];

function renderLanguageChart(langData) {
    const ctx = document.getElementById('languageChart').getContext('2d');
    if (langChartInstance) langChartInstance.destroy();

    const sorted = Object.entries(langData).sort((a, b) => b[1] - a[1]);
    const TOP = 8;
    let labels = sorted.slice(0, TOP).map(([l]) => l);
    let data   = sorted.slice(0, TOP).map(([, v]) => v);

    if (sorted.length > TOP) {
        const otherSum = sorted.slice(TOP).reduce((a, [, v]) => a + v, 0);
        labels.push('Other'); data.push(otherSum);
    }
    if (!labels.length) { labels = ['Unknown']; data = [1]; }

    langChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: CHART_COLORS,
                borderWidth: 2,
                borderColor: 'rgba(0,0,0,0.3)',
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12, padding: 12,
                        font: { size: 12, family: 'Inter' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct   = ((ctx.raw / total) * 100).toFixed(1);
                            return ` ${ctx.label}: ${pct}%`;
                        }
                    }
                }
            }
        }
    });
}

function renderRepoChart(repos) {
    const ctx = document.getElementById('repoChart').getContext('2d');
    if (repoChartInstance) repoChartInstance.destroy();

    const topRepos = [...repos]
        .filter(r => r.stargazers_count > 0)
        .sort((a, b) => b.stargazers_count - a.stargazers_count)
        .slice(0, 10);

    const labels = topRepos.map(r => r.name.length > 18 ? r.name.substring(0, 18) + '…' : r.name);
    const data   = topRepos.map(r => r.stargazers_count);

    if (!labels.length) { labels.push('No starred repos'); data.push(0); }

    repoChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Stars',
                data,
                backgroundColor: CHART_COLORS.slice(0, labels.length),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ⭐ ${ctx.raw} stars`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11, family: 'Inter' } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { font: { size: 11, family: 'Inter' } }
                }
            }
        }
    });
}

// ── Helpers ───────────────────────────────────────────────────────────────
function formatNumber(num) {
    if (!num && num !== 0) return '—';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
    if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'K';
    return num.toString();
}

// ── GitHub Contribution Heatmap ───────────────────────────────────────────
/*
  Uses ghchart.rshah.org — a reliable free service that renders GitHub
  contribution graphs as SVG images (same data as GitHub profile page).
  Fallback: show a friendly message if the service is unavailable.
*/
function renderContributionHeatmap(username) {
    const wrap     = document.getElementById('streak-img-wrap');
    const metaEl   = document.getElementById('streak-meta');
    const card     = document.getElementById('streak-card');
    if (!wrap || !card) return;

    // Show loading state
    wrap.innerHTML = `
        <div class="streak-loading">
            <div class="streak-spinner"></div>
            <span>Loading contribution data…</span>
        </div>`;

    // Theme-aware color: use a purple palette matching our UI
    const color = '7c3aed';

    const img = new Image();
    img.alt   = `${username} GitHub contribution chart`;
    img.title = 'GitHub contribution activity (past year)';
    img.className = 'contribution-img';

    // Primary source: ghchart.rshah.org
    const primarySrc  = `https://ghchart.rshah.org/${color}/${username}`;
    // Fallback source: github-readme-streak-stats embedded
    const fallbackSrc = `https://streak-stats.demolab.com?user=${username}&theme=dark&hide_border=true&date_format=j%20M%5B%20Y%5D&background=00000000&stroke=7c3aed&ring=7c3aed&fire=06b6d4&currStreakNum=e2e8f0&sideNums=e2e8f0&currStreakLabel=94a3b8&sideLabels=94a3b8&dates=64748b`;

    img.onload = () => {
        wrap.innerHTML = '';
        wrap.appendChild(img);
        metaEl.textContent = `📊 Showing last 12 months of contribution activity for @${username}`;
        card.classList.remove('hidden');
    };

    img.onerror = () => {
        // Try fallback streak stats card
        const fallbackImg = new Image();
        fallbackImg.src       = fallbackSrc;
        fallbackImg.alt       = 'GitHub Streak Stats';
        fallbackImg.className = 'contribution-img streak-fallback-img';
        fallbackImg.onload = () => {
            wrap.innerHTML = '';
            wrap.appendChild(fallbackImg);
            metaEl.textContent = `🔥 GitHub Streak Stats for @${username}`;
        };
        fallbackImg.onerror = () => {
            wrap.innerHTML = `
                <div class="streak-unavailable">
                    <span class="streak-unav-icon">🔌</span>
                    <p>Contribution graph unavailable</p>
                    <a href="https://github.com/${username}" target="_blank" rel="noopener">
                        View on GitHub ↗
                    </a>
                </div>`;
            metaEl.textContent = '';
        };
    };

    img.src = primarySrc;
}

function showLoading()   { emptyState.classList.add('hidden'); dashboard.classList.add('hidden'); loading.classList.remove('hidden'); }
function hideLoading()   { loading.classList.add('hidden'); }
function showDashboard() { dashboard.classList.remove('hidden'); }
function showError(msg)  { errorMessage.textContent = msg; errorMessage.classList.remove('hidden'); emptyState.classList.remove('hidden'); dashboard.classList.add('hidden'); }
function hideError()     { errorMessage.classList.add('hidden'); }
