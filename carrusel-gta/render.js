const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+__dirname+'/slides.html');await p.evaluate(()=>document.fonts.ready);
for(const i of [1,2,3]){await p.locator('#s'+i).screenshot({path:`slide-${i}.png`});}
await b.close();})();
