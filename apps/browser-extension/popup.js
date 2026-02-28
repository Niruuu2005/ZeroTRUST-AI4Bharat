const DEFAULT_API = 'http://localhost:3000';

async function getApiBase() {
  const { apiBase } = await chrome.storage.local.get({ apiBase: DEFAULT_API });
  return apiBase.replace(/\/$/, '');
}

function $(id) {
  return document.getElementById(id);
}

function setStatus(msg, isError = false) {
  const el = $('status');
  el.textContent = msg;
  el.style.color = isError ? '#dc2626' : '#64748b';
}

function showResult(data) {
  const result = $('result');
  $('score').textContent = data.credibility_score ?? '—';
  $('category').textContent = data.category ?? '—';
  $('recommendation').textContent = data.recommendation || '';
  $('cached').classList.toggle('hidden', !data.cached);
  result.classList.remove('hidden');
}

$('verify').addEventListener('click', async () => {
  const claim = $('claim').value.trim();
  const type = $('type').value;
  if (claim.length < 10) {
    setStatus('Enter at least 10 characters.', true);
    return;
  }
  const btn = $('verify');
  btn.disabled = true;
  setStatus('Verifying…');
  try {
    const base = await getApiBase();
    const res = await fetch(`${base}/api/v1/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: claim, type, source: 'extension' }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(data.error || data.message || `Error ${res.status}`, true);
      return;
    }
    setStatus('Done.');
    showResult(data);
  } catch (e) {
    setStatus('Network error: ' + e.message, true);
  } finally {
    btn.disabled = false;
  }
});

$('settings').addEventListener('click', (e) => {
  e.preventDefault();
  const base = prompt('API base URL (e.g. http://localhost:3000):', await getApiBase());
  if (base != null) chrome.storage.local.set({ apiBase: base.trim() || DEFAULT_API });
});

// Load saved API URL on open
getApiBase();
