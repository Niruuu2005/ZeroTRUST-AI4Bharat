# ZeroTRUST Browser Extension (Chrome MV3)

Verify claims from the browser: paste text or a URL and get a credibility score from the ZeroTRUST API.

## Install (development)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `apps/browser-extension` folder
4. Pin the extension to the toolbar and click it to open the popup

## Usage

- Enter claim text or a URL (at least 10 characters)
- Choose **Text** or **URL**
- Click **Verify**. The popup shows score, verdict, and recommendation.
- Use **API URL settings** to point to your API (default: `http://localhost:3000`). For production, set your deployed API base URL.

## Permissions

- **storage** — save API base URL
- **host_permissions** — call the API (localhost and https)

## Optional: icons

To add custom icons, create `icons/icon16.png` and `icons/icon48.png`, then add to `manifest.json`:

```json
"action": { "default_popup": "popup.html", "default_icon": { "16": "icons/icon16.png", "48": "icons/icon48.png" } },
"icons": { "16": "icons/icon16.png", "48": "icons/icon48.png" }
```
