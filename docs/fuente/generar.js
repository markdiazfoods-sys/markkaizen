// Genera docs/Manual_de_Marca_MARK_KAIZEN.pdf (A4) a partir de docs/fuente/manual.html.
// Uso: node docs/fuente/generar.js   (necesita Playwright con Chromium)
const {chromium}=require('playwright');const path=require('path');
(async()=>{
 const b=await chromium.launch();const p=await b.newPage();
 await p.goto('file://'+path.join(__dirname,'manual.html'),{waitUntil:'load'});
 await p.evaluate(()=>document.fonts.ready);
 // aviso si algo se sale de la página (deja 14 mm libres para el pie)
 const fuera=await p.evaluate(()=>[...document.querySelectorAll('.page')].map((pg,i)=>{const r=pg.getBoundingClientRect(),lim=r.bottom-14*r.height/297;let m=0;pg.querySelectorAll('.sec,.url').forEach(e=>{m=Math.max(m,e.getBoundingClientRect().bottom-lim)});return m>0?`página ${i+1}: sobran ${Math.round(m*297/r.height)} mm`:null}).filter(Boolean));
 if(fuera.length)console.warn('Contenido fuera de página →',fuera.join(' · '));
 await p.pdf({path:path.join(__dirname,'..','Manual_de_Marca_MARK_KAIZEN.pdf'),format:'A4',printBackground:true,preferCSSPageSize:true,margin:{top:0,right:0,bottom:0,left:0}});
 await b.close();console.log('PDF generado');
})();
