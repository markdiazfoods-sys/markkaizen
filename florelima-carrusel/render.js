const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1500 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'index.html'));
  await p.waitForLoadState('networkidle').catch(() => {});
  await p.evaluate(() => document.fonts.ready);
  console.log('Anton loaded:', await p.evaluate(() => document.fonts.check("40px Anton")));
  for (let i = 1; i <= 5; i++) {
    await p.locator('#s' + i).screenshot({ path: path.join(__dirname, `slide-${i}.png`) });
  }
  await b.close();
})();
