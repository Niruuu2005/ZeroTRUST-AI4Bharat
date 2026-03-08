// ─────────────────────────────────────────────────────────────────────────────
// ZeroTrust AI — Popup Script
// ─────────────────────────────────────────────────────────────────────────────

const VERDICT_COLORS = {
  SUPPORTED:    { hex: '#22c55e', label: 'Supported',   icon: '✓' },
  NEUTRAL:      { hex: '#f59e0b', label: 'Neutral',      icon: '~' },
  CONTRADICTED: { hex: '#ef4444', label: 'Contradicted', icon: '✗' },
  ERROR:        { hex: '#6b7280', label: 'Error',         icon: '!' },
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const panelMain      = document.getElementById('panel-main');
const panelSettings  = document.getElementById('panel-settings');
const verifyInput    = document.getElementById('verify-input');
const verifyBtn      = document.getElementById('verify-btn');
const loadingState   = document.getElementById('loading-state');
const resultCard     = document.getElementById('result-card');
const historyList    = document.getElementById('history-list');
const openSidebarBtn = document.getElementById('open-sidebar-btn');
const openSettingsBtn= document.getElementById('open-settings');
const backBtn        = document.getElementById('back-btn');
const saveSettingsBtn= document.getElementById('save-settings');
const apiKeyInput    = document.getElementById('api-key-input');
const apiBaseInput   = document.getElementById('api-base-input');
const toggleAutoscan = document.getElementById('toggle-autoscan');
const toggleHighlight= document.getElementById('toggle-highlight');

// ── Panel nav ─────────────────────────────────────────────────────────────────
openSettingsBtn.addEventListener('click', () => {
  panelMain.classList.remove('active');
  panelSettings.classList.add('active');
  loadSettings();
});

backBtn.addEventListener('click', () => {
  panelSettings.classList.remove('active');
  panelMain.classList.add('active');
});

// ── Tab switch ────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const type = tab.dataset.tab;
    verifyInput.placeholder = type === 'image'
      ? 'Paste an image URL to check for deepfake / manipulation…'
      : 'Paste a claim, article URL, or any text to verify…';
  });
});

// ── Verify ────────────────────────────────────────────────────────────────────
verifyBtn.addEventListener('click', runVerify);

verifyInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runVerify();
});

function runVerify() {
  const query = verifyInput.value.trim();
  if (!query) return;

  const activeTab = document.querySelector('.tab.active');
  const inputType = activeTab?.dataset.tab ?? 'text';
  const type = inputType === 'image' ? 'image' : (isURL(query) ? 'url' : 'text');

  showLoading();

  chrome.runtime.sendMessage(
    { action: 'VERIFY', payload: { type, query } },
    (response) => {
      hideLoading();
      if (response?.ok) {
        renderResult(response.result);
      } else {
        renderResult({
          verdict: 'ERROR',
          score: 0,
          summary: response?.error ?? 'An error occurred. Please try again.',
          agents: [],
        });
      }
    }
  );
}

function isURL(str) {
  try { new URL(str); return true; } catch { return false; }
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function showLoading() {
  verifyBtn.disabled = true;
  resultCard.classList.add('hidden');
  loadingState.classList.remove('hidden');
}

function hideLoading() {
  verifyBtn.disabled = false;
  loadingState.classList.add('hidden');
}

function renderResult(result) {
  const c   = VERDICT_COLORS[result.verdict] ?? VERDICT_COLORS.ERROR;
  const pct = Math.round((result.score ?? 0) * 100);

  // Chip
  const chip = document.getElementById('result-chip');
  chip.textContent = `${c.icon}  ${c.label}`;
  chip.style.cssText = `background:${c.hex}20; color:${c.hex}; border-color:${c.hex}40`;

  // Score
  document.getElementById('result-score').textContent = `${pct}%`;
  const fill = document.getElementById('score-fill');
  fill.style.width   = '0%';
  fill.style.background = c.hex;
  requestAnimationFrame(() => { fill.style.width = `${pct}%`; });

  // Summary
  document.getElementById('result-summary').textContent = result.summary ?? '';

  // Agents
  const agentList = document.getElementById('agent-list');
  agentList.innerHTML = (result.agents ?? []).map(a => {
    const ac = VERDICT_COLORS[a.verdict] ?? VERDICT_COLORS.NEUTRAL;
    return `
      <div class="agent-row">
        <span class="agent-dot" style="background:${ac.hex}"></span>
        <span class="agent-name">${a.name}</span>
      </div>`;
  }).join('');

  resultCard.classList.remove('hidden');
  refreshHistory();
}

// ── Open sidebar ──────────────────────────────────────────────────────────────
openSidebarBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]?.id) {
      chrome.sidePanel.open({ tabId: tabs[0].id });
      window.close();
    }
  });
});

// ── History ───────────────────────────────────────────────────────────────────
function refreshHistory() {
  chrome.storage.local.get('verifyHistory', ({ verifyHistory = [] }) => {
    if (!verifyHistory.length) {
      historyList.innerHTML = '<p class="empty-msg">No verifications yet.</p>';
      return;
    }
    historyList.innerHTML = verifyHistory.slice(0, 6).map(item => {
      const c = VERDICT_COLORS[item.verdict] ?? VERDICT_COLORS.ERROR;
      return `
        <div class="history-item">
          <span class="history-dot" style="background:${c.hex}"></span>
          <span class="history-query">${escapeHtml(item.query)}</span>
          <span class="history-verdict" style="color:${c.hex}">${c.label}</span>
        </div>`;
    }).join('');
  });
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Settings ──────────────────────────────────────────────────────────────────
function loadSettings() {
  chrome.storage.local.get('settings', ({ settings = {} }) => {
    apiKeyInput.value  = settings.apiKey  ?? '';
    apiBaseInput.value = settings.apiBase ?? 'http://localhost:8000';
    setToggle(toggleAutoscan,  !!settings.autoScan);
    setToggle(toggleHighlight, !!settings.highlightClaims);
  });
}

toggleAutoscan.addEventListener('click', () => toggleAutoscan.classList.toggle('on'));
toggleHighlight.addEventListener('click', () => toggleHighlight.classList.toggle('on'));

function setToggle(el, on) {
  on ? el.classList.add('on') : el.classList.remove('on');
}

saveSettingsBtn.addEventListener('click', () => {
  const newSettings = {
    apiKey:          apiKeyInput.value.trim(),
    apiBase:         apiBaseInput.value.trim() || 'http://localhost:8000',
    autoScan:        toggleAutoscan.classList.contains('on'),
    highlightClaims: toggleHighlight.classList.contains('on'),
    showBadge:       true,
  };
  chrome.storage.local.set({ settings: newSettings }, () => {
    saveSettingsBtn.textContent = 'Saved ✓';
    setTimeout(() => { saveSettingsBtn.textContent = 'Save Settings'; }, 1500);
    panelSettings.classList.remove('active');
    panelMain.classList.add('active');
  });
});

// ── Init ──────────────────────────────────────────────────────────────────────
refreshHistory();

// Pre-fill from any pending verify (triggered via context menu)
chrome.storage.session.get('pendingVerify', ({ pendingVerify }) => {
  if (pendingVerify?.query) {
    verifyInput.value = pendingVerify.query;
    chrome.storage.session.remove('pendingVerify');
    runVerify();
  }
});
