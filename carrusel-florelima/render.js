// Renderiza cada slide a PNG 1080x1350 (formato Instagram 4:5)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'carrusel.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  for (let i = 1; i <= 7; i++) {
    await p.locator('#s' + i).screenshot({ path: `salida/slide-${i}.png` });
  }
  await b.close();
})();
