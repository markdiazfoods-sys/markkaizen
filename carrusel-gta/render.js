// Exporta cada lámina a PNG 1080x1350. Uso: node render.js   (requiere playwright)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1180, height: 1500 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'index.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(600);
  for (let i = 1; i <= 6; i++) {
    await p.locator('#s' + i).screenshot({ path: path.join(__dirname, `slide-${i}.png`) });
  }
  await b.close();
  console.log('ok: 6 láminas');
})();
