// Renderiza los 3 slides a PNG 1080x1920. Uso: node render.js
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();
 const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
 await p.goto('file://'+path.join(__dirname,'carrusel.html'));await p.waitForTimeout(800);
 for(const n of [1,2,3]){await p.locator('#s'+n).screenshot({path:path.join(__dirname,`slide-${n}.png`)});}
 await b.close();console.log('ok');})();
