# ZeroTrust AI — Browser Extension

Chrome Manifest V3 browser extension for real-time fact verification, deepfake detection, and source credibility analysis powered by the 6-agent ZeroTrust backend.

---

## Structure

```
extension/
├── manifest.json              # Chrome MV3 manifest
├── background/
│   └── background.js          # Service worker: context menus, API relay, badge, history
├── content/
│   ├── content.js             # Injected into every page: tooltip, overlay, verdict card
│   └── content.css            # Styles for injected UI elements
├── popup/
│   ├── popup.html             # Extension popup (click toolbar icon)
│   ├── popup.css
│   └── popup.js
├── sidebar/
│   ├── sidebar.html           # Side panel (Chrome side panel API)
│   ├── sidebar.css
│   └── sidebar.js
└── icons/
    ├── icon.svg               # Source SVG icon
    ├── generate-icons.js      # Script to convert SVG → PNG at 16/32/48/128px
    ├── icon16.png             # ← generate these (see below)
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

---

## Setup

### 1. Generate Icons

```bash
cd extension/icons
npm install sharp
node generate-icons.js
```

Or convert `icon.svg` manually at 16×16, 32×32, 48×48, 128×128 and save as `icon16.png` etc.

### 2. Add API Key (optional for dev)

Leave blank to use mock responses during development. Add your real key in the extension Settings panel once loaded.

### 3. Load in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder

### 4. Load in Edge

Same process via `edge://extensions`.

### 5. Load in Brave

Same process via `brave://extensions`.

---

## Features

| Feature              | How to use                                                        |
| -------------------- | ----------------------------------------------------------------- |
| Verify selected text | Select text on any page → click **Verify with ZeroTrust** tooltip |
| Keyboard shortcut    | Select text → `Ctrl+Shift+V` (Mac: `Cmd+Shift+V`)                 |
| Verify a link        | Right-click any link → **Verify this link with ZeroTrust AI**     |
| Verify current page  | Right-click page → **Verify current page with ZeroTrust AI**      |
| Deepfake check       | Right-click any image → **Check image for deepfakes**             |
| Popup                | Click toolbar icon → paste claim/URL → VERIFY NOW                 |
| Side panel           | Opens automatically on context menu / shortcut; shows full report |

---

## Backend Integration

Replace `API_BASE` in `background/background.js`:

```js
const API_BASE = "https://your-zerotrust-backend.com/v1";
```

The extension POSTs to `POST /verify` with:

```json
{
  "type": "text|url|image",
  "query": "..."
}
```

Expected response shape:

```json
{
  "verdict": "SUPPORTED|NEUTRAL|CONTRADICTED",
  "score": 0.82,
  "confidence": 0.91,
  "summary": "...",
  "agents": [
    { "name": "NewsAgent", "verdict": "SUPPORTED", "score": 0.85 },
    ...
  ],
  "sources": ["https://..."]
}
```
