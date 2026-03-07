// ─────────────────────────────────────────────────────────────────────────────
// ZeroTrust AI — Content Script
// Injected into every page. Handles:
//   • Selection tooltip button
//   • Loading overlay
//   • Verdict overlay (pinned card on page)
//   • Message relay to/from background
// ─────────────────────────────────────────────────────────────────────────────

(function () {
  'use strict';

  // Avoid double-injection
  if (window.__zerotrust_injected) return;
  window.__zerotrust_injected = true;

  // ── State ──────────────────────────────────────────────────────────────────
  let tooltipEl    = null;
  let overlayEl    = null;
  let verdictEl    = null;
  let lastSelection = '';

  // ── Tooltip: shows "Verify" button on text selection ──────────────────────
  document.addEventListener('mouseup', (e) => {
    const sel = window.getSelection();
    const text = sel?.toString().trim();

    if (!text || text.length < 10) {
      removeTooltip();
      return;
    }

    if (text === lastSelection) return;
    lastSelection = text;

    removeTooltip();

    const range  = sel.getRangeAt(0);
    const rect   = range.getBoundingClientRect();

    tooltipEl = buildTooltip();
    document.body.appendChild(tooltipEl);

    const scrollX = window.scrollX;
    const scrollY = window.scrollY;
    const left    = rect.left + scrollX + rect.width / 2 - tooltipEl.offsetWidth / 2;
    const top     = rect.top  + scrollY - tooltipEl.offsetHeight - 10;

    tooltipEl.style.left = `${Math.max(8, left)}px`;
    tooltipEl.style.top  = `${Math.max(8, top)}px`;
    tooltipEl.style.opacity = '1';

    tooltipEl.querySelector('#zt-verify-btn').addEventListener('click', () => {
      removeTooltip();
      sendVerify({ type: 'text', query: text });
    });
  });

  document.addEventListener('mousedown', (e) => {
    if (tooltipEl && !tooltipEl.contains(e.target)) {
      removeTooltip();
      lastSelection = '';
    }
  });

  function buildTooltip() {
    const el = document.createElement('div');
    el.id = 'zt-tooltip';
    el.innerHTML = `
      <button id="zt-verify-btn">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        Verify with ZeroTrust
      </button>
    `;
    return el;
  }

  function removeTooltip() {
    tooltipEl?.remove();
    tooltipEl = null;
  }

  // ── Loading overlay ────────────────────────────────────────────────────────
  function showLoadingOverlay() {
    removeLoadingOverlay();
    overlayEl = document.createElement('div');
    overlayEl.id = 'zt-loading-overlay';
    overlayEl.innerHTML = `
      <div id="zt-loading-card">
        <div class="zt-spinner"></div>
        <div class="zt-loading-text">Analyzing with 6 AI agents…</div>
        <div class="zt-loading-sub">ZeroTrust is processing your request</div>
      </div>
    `;
    document.body.appendChild(overlayEl);
    requestAnimationFrame(() => overlayEl.classList.add('zt-visible'));
  }

  function removeLoadingOverlay() {
    overlayEl?.remove();
    overlayEl = null;
  }

  // ── Verdict card ───────────────────────────────────────────────────────────
  function showVerdictCard(result) {
    removeVerdictCard();

    const colorMap = {
      SUPPORTED:    { hex: '#22c55e', label: 'Supported',    icon: '✓' },
      NEUTRAL:      { hex: '#f59e0b', label: 'Neutral',       icon: '~' },
      CONTRADICTED: { hex: '#ef4444', label: 'Contradicted',  icon: '✗' },
    };
    const c = colorMap[result.verdict] ?? { hex: '#6b7280', label: 'Unknown', icon: '?' };
    const pct = Math.round((result.score ?? 0) * 100);

    verdictEl = document.createElement('div');
    verdictEl.id = 'zt-verdict-card';
    verdictEl.innerHTML = `
      <div class="zt-verdict-header">
        <div class="zt-verdict-logo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <span class="zt-verdict-brand">ZeroTrust AI</span>
        <button class="zt-close-btn" id="zt-close-verdict">✕</button>
      </div>

      <div class="zt-verdict-body">
        <div class="zt-verdict-chip" style="background:${c.hex}20; color:${c.hex}; border-color:${c.hex}40">
          <span class="zt-verdict-icon">${c.icon}</span>
          ${c.label}
        </div>

        <div class="zt-score-bar">
          <div class="zt-score-fill" style="width:${pct}%; background:${c.hex}"></div>
        </div>
        <div class="zt-score-label">Credibility score: <strong>${pct}%</strong></div>

        <p class="zt-summary">${result.summary ?? ''}</p>

        <div class="zt-agents">
          ${(result.agents ?? []).map(a => `
            <div class="zt-agent-row">
              <span class="zt-agent-dot" style="background:${(colorMap[a.verdict] ?? colorMap.NEUTRAL).hex}"></span>
              <span class="zt-agent-name">${a.name}</span>
            </div>
          `).join('')}
        </div>

        <button class="zt-open-sidebar" id="zt-open-sidebar-btn">
          View full report →
        </button>
      </div>
    `;

    document.body.appendChild(verdictEl);
    requestAnimationFrame(() => verdictEl.classList.add('zt-visible'));

    verdictEl.querySelector('#zt-close-verdict').addEventListener('click', removeVerdictCard);
    verdictEl.querySelector('#zt-open-sidebar-btn').addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'OPEN_SIDEBAR' });
    });
  }

  function removeVerdictCard() {
    verdictEl?.remove();
    verdictEl = null;
  }

  // ── Send verify request via background ────────────────────────────────────
  function sendVerify(payload) {
    showLoadingOverlay();
    chrome.runtime.sendMessage({ action: 'VERIFY', payload }, (response) => {
      removeLoadingOverlay();
      if (response?.ok) {
        showVerdictCard(response.result);
      } else {
        showVerdictCard({
          verdict: 'ERROR',
          score: 0,
          summary: response?.error ?? 'Something went wrong. Please try again.',
          agents: [],
        });
      }
    });
  }

  // ── Listen for messages from background ───────────────────────────────────
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'SHOW_LOADING_OVERLAY') {
      showLoadingOverlay();
    }
  });
})();
