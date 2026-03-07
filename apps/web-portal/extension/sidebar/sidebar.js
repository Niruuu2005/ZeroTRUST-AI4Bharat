// ─────────────────────────────────────────────────────────────────────────────
// ZeroTrust AI — Sidebar Script
// ─────────────────────────────────────────────────────────────────────────────

const VERDICT_COLORS = {
  SUPPORTED:    { hex: '#22c55e', label: 'Supported',   icon: '✓' },
  NEUTRAL:      { hex: '#f59e0b', label: 'Neutral',      icon: '~' },
  CONTRADICTED: { hex: '#ef4444', label: 'Contradicted', icon: '✗' },
  ERROR:        { hex: '#6b7280', label: 'Error',         icon: '!' },
};

// ── State ─────────────────────────────────────────────────────────────────────
let currentResult  = null;
let currentQuery   = '';

// ── DOM refs ──────────────────────────────────────────────────────────────────
const views          = document.querySelectorAll('.view');
const navBtns        = document.querySelectorAll('.nav-btn');
const statusDot      = document.getElementById('status-dot');
const statusLabel    = document.getElementById('status-label');
const quickInput     = document.getElementById('quick-input');
const quickVerifyBtn = document.getElementById('quick-verify-btn');
const agentSteps     = document.querySelectorAll('.agent-step');
const historyList    = document.getElementById('history-list');
const clearHistoryBtn= document.getElementById('clear-history-btn');
const reVerifyBtn    = document.getElementById('re-verify-btn');
const newVerifyBtn   = document.getElementById('new-verify-btn');

// ── Navigation ─────────────────────────────────────────────────────────────────
function showView(name) {
  views.forEach(v  => v.classList.remove('active'));
  navBtns.forEach(b => b.classList.remove('active'));

  const view = document.getElementById(`view-${name}`);
  const btn  = document.querySelector(`.nav-btn[data-view="${name}"]`);
  if (view) view.classList.add('active');
  if (btn)  btn.classList.add('active');
}

navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.view;
    if (target === 'result' && !currentResult) return; // no result yet
    if (target === 'history') refreshHistory();
    showView(target);
  });
});

// ── Quick verify ─────────────────────────────────────────────────────────────
quickVerifyBtn.addEventListener('click', startVerify);
quickInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startVerify();
});

function startVerify() {
  const query = quickInput.value.trim();
  if (!query) return;
  currentQuery = query;
  runVerify({ type: isURL(query) ? 'url' : 'text', query });
}

function isURL(str) {
  try { new URL(str); return true; } catch { return false; }
}

// ── Run verify ────────────────────────────────────────────────────────────────
function runVerify(payload) {
  showView('loading');
  setStatus('active', 'Analyzing…');
  animateAgentSteps();

  chrome.runtime.sendMessage({ action: 'VERIFY', payload }, (response) => {
    stopAgentAnimation();
    if (response?.ok) {
      currentResult = response.result;
      renderResult(response.result, payload.query);
      setStatus('done', 'Complete');
      showView('result');
    } else {
      currentResult = {
        verdict: 'ERROR', score: 0,
        summary: response?.error ?? 'Something went wrong.',
        agents: [],
      };
      renderResult(currentResult, payload.query);
      setStatus('error', 'Error');
      showView('result');
    }

    // Re-enable nav result button
    document.getElementById('nav-result').disabled = false;
  });
}

// ── Agent step animation ───────────────────────────────────────────────────────
let stepTimer = null;
let stepIndex  = 0;

function animateAgentSteps() {
  agentSteps.forEach(s => s.classList.remove('active', 'done'));
  stepIndex = 0;
  stepTimer = setInterval(() => {
    if (stepIndex < agentSteps.length) {
      if (stepIndex > 0) agentSteps[stepIndex - 1].classList.remove('active');
      if (stepIndex > 0) agentSteps[stepIndex - 1].classList.add('done');
      agentSteps[stepIndex].classList.add('active');
      stepIndex++;
    }
  }, 300);
}

function stopAgentAnimation() {
  clearInterval(stepTimer);
  agentSteps.forEach(s => { s.classList.remove('active'); s.classList.add('done'); });
}

// ── Render result ─────────────────────────────────────────────────────────────
function renderResult(result, query) {
  const c   = VERDICT_COLORS[result.verdict] ?? VERDICT_COLORS.ERROR;
  const pct = Math.round((result.score ?? 0) * 100);
  const circumference = 2 * Math.PI * 42; // r=42

  // Banner
  const banner = document.getElementById('verdict-banner');
  banner.style.background     = `${c.hex}12`;
  banner.style.borderBottomColor = `${c.hex}20`;

  const iconWrap = document.getElementById('verdict-icon-wrap');
  iconWrap.style.background = `${c.hex}20`;

  document.getElementById('verdict-label').textContent = c.label.toUpperCase();
  document.getElementById('verdict-label').style.color = c.hex;
  document.getElementById('verdict-score').textContent = `Credibility: ${pct}%`;

  // Score ring
  const arc = document.getElementById('score-ring-arc');
  arc.style.stroke = c.hex;
  const dashLen = (pct / 100) * circumference;
  requestAnimationFrame(() => {
    arc.style.transition = 'stroke-dasharray 1s ease';
    arc.setAttribute('stroke-dasharray', `${dashLen} ${circumference}`);
  });
  document.getElementById('score-pct').textContent = `${pct}%`;
  document.getElementById('score-pct').style.color  = c.hex;

  // Summary
  document.getElementById('result-summary').textContent = result.summary ?? '';

  // Agent breakdown
  const breakdown = document.getElementById('agent-breakdown');
  breakdown.innerHTML = (result.agents ?? []).map(a => {
    const ac = VERDICT_COLORS[a.verdict] ?? VERDICT_COLORS.NEUTRAL;
    return `
      <div class="ab-row">
        <span class="ab-dot" style="background:${ac.hex}"></span>
        <span class="ab-name">${a.name}</span>
        <span class="ab-verdict" style="color:${ac.hex}">${ac.label}</span>
      </div>`;
  }).join('');

  // Sources
  const sourcesSec  = document.getElementById('sources-section');
  const sourcesList = document.getElementById('sources-list');
  if (result.sources?.length) {
    sourcesSec.style.display = 'block';
    sourcesList.innerHTML = result.sources.slice(0, 5).map(s =>
      `<a class="source-link" href="${escapeHtml(s)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s)}</a>`
    ).join('');
  } else {
    sourcesSec.style.display = 'none';
  }

  // Query
  document.getElementById('result-query').textContent = (query ?? currentQuery ?? '').slice(0, 300);
}

// ── Status ────────────────────────────────────────────────────────────────────
function setStatus(state, label) {
  statusDot.className = `status-dot ${state}`;
  statusLabel.textContent = label;
}

// ── Re-verify / New verify ────────────────────────────────────────────────────
reVerifyBtn.addEventListener('click', () => {
  if (currentQuery) runVerify({ type: isURL(currentQuery) ? 'url' : 'text', query: currentQuery });
});

newVerifyBtn.addEventListener('click', () => {
  quickInput.value = '';
  currentResult = null;
  currentQuery  = '';
  setStatus('', 'Idle');
  showView('idle');
});

// ── History ───────────────────────────────────────────────────────────────────
function refreshHistory() {
  chrome.storage.local.get('verifyHistory', ({ verifyHistory = [] }) => {
    if (!verifyHistory.length) {
      historyList.innerHTML = '<p class="empty-msg">No history yet.</p>';
      return;
    }
    historyList.innerHTML = verifyHistory.slice(0, 30).map(item => {
      const c    = VERDICT_COLORS[item.verdict] ?? VERDICT_COLORS.ERROR;
      const time = formatTime(item.ts);
      return `
        <div class="history-item" data-query="${escapeHtml(item.query)}" data-type="${item.type}">
          <div class="history-item-top">
            <span class="history-dot" style="background:${c.hex}"></span>
            <span class="history-verdict-label" style="color:${c.hex}">${c.label}</span>
            <span class="history-time">${time}</span>
          </div>
          <div class="history-query">${escapeHtml(item.query)}</div>
        </div>`;
    }).join('');

    // Click to re-verify
    document.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', () => {
        const q = item.dataset.query;
        const t = item.dataset.type;
        currentQuery = q;
        quickInput.value = q;
        runVerify({ type: t, query: q });
      });
    });
  });
}

clearHistoryBtn.addEventListener('click', () => {
  chrome.storage.local.set({ verifyHistory: [] }, () => {
    historyList.innerHTML = '<p class="empty-msg">No history yet.</p>';
  });
});

function formatTime(iso) {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60)   return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400)return `${Math.floor(diff / 3600)}h ago`;
    return d.toLocaleDateString();
  } catch { return ''; }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init: check for pending verify or last verdict ────────────────────────────
chrome.storage.session.get(['pendingVerify', 'lastVerdict'], (data) => {
  if (data.pendingVerify?.query) {
    currentQuery = data.pendingVerify.query;
    quickInput.value = currentQuery;
    chrome.storage.session.remove('pendingVerify');
    runVerify(data.pendingVerify);
  } else if (data.lastVerdict) {
    currentResult = data.lastVerdict;
    renderResult(data.lastVerdict, '');
    setStatus('done', 'Complete');
    showView('result');
  } else {
    showView('idle');
  }
});
