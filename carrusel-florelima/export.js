// Exporta cada lámina a PNG 1080x1350 y todo el carrusel a un PDF.
// Uso: node export.js   (requiere playwright)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1500 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'index.html'));
  await p.evaluate(() => document.fonts.ready);
  const n = await p.locator('.s').count();
  for (let i = 0; i < n; i++) {
    await p.locator('.s').nth(i).screenshot({ path: `export/lamina-${i + 1}.png` });
  }
  await p.pdf({ path: 'export/carrusel-florelima.pdf', width: '1080px', height: '1350px', printBackground: true });
  await b.close();
  console.log(`${n} láminas exportadas`);
})();
