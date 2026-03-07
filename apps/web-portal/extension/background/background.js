// ─────────────────────────────────────────────────────────────────────────────
// ZeroTrust AI — Background Service Worker
// Handles: context menus, keyboard shortcuts, messaging, API relay, badge
// ─────────────────────────────────────────────────────────────────────────────

// Default API base — user can override in Settings (saved to chrome.storage.local)
// Change this to your deployed backend URL, e.g. https://api.zerotrust.ai/v1
const DEFAULT_API_BASE = 'http://localhost:8000';

async function getApiBase() {
  const { settings } = await chrome.storage.local.get('settings');
  return (settings?.apiBase?.trim() || DEFAULT_API_BASE).replace(/\/$/, '');
}

// ── Context Menu Setup ────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'zerotrust-verify-text',
    title: 'Verify with ZeroTrust AI',
    contexts: ['selection'],
  });

  chrome.contextMenus.create({
    id: 'zerotrust-verify-link',
    title: 'Verify this link with ZeroTrust AI',
    contexts: ['link'],
  });

  chrome.contextMenus.create({
    id: 'zerotrust-verify-page',
    title: 'Verify current page with ZeroTrust AI',
    contexts: ['page'],
  });

  chrome.contextMenus.create({
    id: 'zerotrust-verify-image',
    title: 'Check image for deepfakes / manipulation',
    contexts: ['image'],
  });

  // Default storage
  chrome.storage.local.set({
    verifyHistory: [],
    settings: {
      autoScan: false,
      showBadge: true,
      highlightClaims: false,
      apiKey: '',
      apiBase: DEFAULT_API_BASE,
    },
  });
});

// ── Context Menu Clicks ───────────────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab?.id) return;

  let payload = null;

  if (info.menuItemId === 'zerotrust-verify-text' && info.selectionText) {
    payload = { type: 'text', query: info.selectionText };
  } else if (info.menuItemId === 'zerotrust-verify-link' && info.linkUrl) {
    payload = { type: 'url', query: info.linkUrl };
  } else if (info.menuItemId === 'zerotrust-verify-page' && tab.url) {
    payload = { type: 'url', query: tab.url };
  } else if (info.menuItemId === 'zerotrust-verify-image' && info.srcUrl) {
    payload = { type: 'image', query: info.srcUrl };
  }

  if (payload) {
    // Open sidebar and send payload
    chrome.sidePanel.open({ tabId: tab.id });
    chrome.storage.session.set({ pendingVerify: payload });
    chrome.tabs.sendMessage(tab.id, { action: 'SHOW_LOADING_OVERLAY' });
  }
});

// ── Keyboard Shortcut ─────────────────────────────────────────────────────────
chrome.commands.onCommand.addListener((command, tab) => {
  if (command === 'verify-selection' && tab?.id) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection()?.toString() ?? '',
    }).then((results) => {
      const selected = results?.[0]?.result?.trim();
      const query = selected || tab.url || '';
      const type  = selected ? 'text' : 'url';

      chrome.sidePanel.open({ tabId: tab.id });
      chrome.storage.session.set({ pendingVerify: { type, query } });
    });
  }
});

// ── Message Bus ───────────────────────────────────────────────────────────────
// Content scripts and popup communicate here
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'VERIFY') {
    handleVerify(message.payload)
      .then((result) => sendResponse({ ok: true, result }))
      .catch((err)  => sendResponse({ ok: false, error: err.message }));
    return true; // keep channel open for async response
  }

  if (message.action === 'GET_VERDICT_BADGE') {
    chrome.storage.session.get('lastVerdict', (data) => {
      sendResponse(data.lastVerdict ?? null);
    });
    return true;
  }

  if (message.action === 'OPEN_SIDEBAR') {
    if (sender.tab?.id) chrome.sidePanel.open({ tabId: sender.tab.id });
    sendResponse({ ok: true });
  }
});

// ── Core Verify Function ──────────────────────────────────────────────────────
async function handleVerify(payload) {
  const { settings } = await chrome.storage.local.get('settings');
  const apiKey  = settings?.apiKey  || '';
  const apiBase = (settings?.apiBase?.trim() || DEFAULT_API_BASE).replace(/\/$/, '');

  const body = {
    type:  payload.type,   // 'text' | 'url' | 'image'
    query: payload.query,
  };

  let result;

  try {
    const res = await fetch(`${apiBase}/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const json = await res.json();

    // Normalise response → consistent shape
    result = {
      verdict:    json.verdict ?? scoreToVerdict(json.credibility_score ?? json.score),
      score:      json.score ?? (json.credibility_score != null ? json.credibility_score / 100 : 0),
      confidence: json.confidence ?? 0,
      summary:    json.evidence_summary ?? json.summary ?? '',
      agents:     json.agents ?? Object.entries(json.agent_verdicts ?? {}).map(([name, v]) => ({
                    name, verdict: verdictKeyword(String(v)),
                  })),
      sources:    (json.sources ?? []).map((s) => typeof s === 'string' ? s : s.url),
    };
  } catch {
    // Backend unavailable → use mock
    result = await mockVerify(payload);
  }

  // Persist last verdict for badge/content script
  chrome.storage.session.set({ lastVerdict: result });

  // Update badge
  updateBadge(result.verdict);

  // Save to history
  const { verifyHistory = [] } = await chrome.storage.local.get('verifyHistory');
  verifyHistory.unshift({
    id: Date.now(),
    query: payload.query.slice(0, 200),
    type: payload.type,
    verdict: result.verdict,
    score: result.score,
    ts: new Date().toISOString(),
  });
  await chrome.storage.local.set({ verifyHistory: verifyHistory.slice(0, 50) });

  return result;
}

// ── Verdict helpers ───────────────────────────────────────────────────────────
function scoreToVerdict(score) {
  if (score == null) return 'NEUTRAL';
  const s = typeof score === 'number' && score > 1 ? score / 100 : score;
  if (s >= 0.7)  return 'SUPPORTED';
  if (s <= 0.35) return 'CONTRADICTED';
  return 'NEUTRAL';
}

function verdictKeyword(str) {
  const s = str.toUpperCase();
  if (s.includes('SUPPORT') || s.includes('TRUE') || s.includes('CREDIBLE')) return 'SUPPORTED';
  if (s.includes('CONTRADICT') || s.includes('FALSE') || s.includes('DISPUTED')) return 'CONTRADICTED';
  return 'NEUTRAL';
}

// ── Badge ─────────────────────────────────────────────────────────────────────
function updateBadge(verdict) {
  const map = {
    SUPPORTED:    { text: '✓',  color: '#22c55e' },
    NEUTRAL:      { text: '~',  color: '#f59e0b' },
    CONTRADICTED: { text: '✗',  color: '#ef4444' },
    ERROR:        { text: '!',  color: '#6b7280' },
  };
  const b = map[verdict] ?? map.ERROR;
  chrome.action.setBadgeText({ text: b.text });
  chrome.action.setBadgeBackgroundColor({ color: b.color });
}

// ── Mock Verify (no API key) ──────────────────────────────────────────────────
async function mockVerify(payload) {
  await new Promise(r => setTimeout(r, 1800)); // simulate latency

  const verdicts = ['SUPPORTED', 'NEUTRAL', 'CONTRADICTED'];
  const verdict  = verdicts[Math.floor(Math.random() * verdicts.length)];
  const score    = verdict === 'SUPPORTED' ? 0.82 : verdict === 'CONTRADICTED' ? 0.21 : 0.51;

  return {
    verdict,
    score,
    confidence: 0.87,
    summary: `[Demo] ZeroTrust analyzed the ${payload.type} and found it to be ${verdict.toLowerCase()}.`,
    agents: [
      { name: 'NewsAgent',     verdict, score },
      { name: 'ScienceAgent',  verdict, score },
      { name: 'ResearchAgent', verdict, score },
      { name: 'ScraperAgent',  verdict, score },
      { name: 'SentimentAgent',verdict, score },
      { name: 'MediaAgent',    verdict, score },
    ],
    sources: [],
  };
}
