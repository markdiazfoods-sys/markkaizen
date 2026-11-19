// Exporta láminas a PNG. Uso: node render.js            -> slide-N.png 1080x1350 (Instagram)
//                          node render.js tiktok     -> tiktok-N.png 1080x1920 (TikTok)
const { chromium } = require('playwright');
const path = require('path');
const tt = process.argv[2] === 'tiktok';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1180, height: tt ? 2100 : 1500 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, tt ? 'tiktok.html' : 'index.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(600);
  for (let i = 1; i <= 6; i++) {
    await p.locator('#s' + i).screenshot({ path: path.join(__dirname, (tt ? `tiktok-${i}` : `slide-${i}`) + '.png') });
  }
  await b.close();
  console.log('ok: 6 láminas');
})();
