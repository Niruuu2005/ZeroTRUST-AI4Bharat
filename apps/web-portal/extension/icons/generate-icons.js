// ─────────────────────────────────────────────────────────────────────────────
// ZeroTrust AI — Icon Generator
// Run: node generate-icons.js   (from extension/icons/)
// Requires: sharp  →  npm install sharp  (in project root)
// Source:   ../../public/logo-transparent.png  (the real project logo)
// ─────────────────────────────────────────────────────────────────────────────

const sharp = require('sharp');
const path  = require('path');

const src   = path.resolve(__dirname, '..', '..', 'public', 'logo-transparent.png');
const sizes = [16, 32, 48, 128];

Promise.all(
  sizes.map(size =>
    sharp(src)
      .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(path.join(__dirname, `icon${size}.png`))
      .then(() => console.log(`✓  icon${size}.png`))
  )
)
.then(() => console.log('\n✅  Icons updated with original project logo.'))
.catch(console.error);
