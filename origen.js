/* Cómo nació MARK KAIZEN: arma la sección dentro de <section class="origin" data-origin> y la anima con el scroll.
   Fases: 1 dragón entra · 2 gato entra · 3 se unen y giran (yin-yang) · 4 brilla 改善 · 5 se cierra el anillo y nace la marca. */
(()=>{const el=document.querySelector("[data-origin]");if(!el)return;
const S=[
 ["01","El <em>dragón</em>","Fuerza, ambición y transformación. Es mi lado <b>estratégico</b>: el que mira los datos, planifica y empuja cada campaña hacia un resultado."],
 ["02","El <em class=\"g\">gato</em>","Curiosidad, intuición y sensibilidad estética. Es mi lado <b>creativo</b>: el que observa, juega con las ideas y cuida cada detalle visual."],
 ["03","Dos fuerzas, <em>un círculo</em>","Durante mucho tiempo parecían opuestas. Pero la estrategia sin creatividad no conecta, y la creatividad sin estrategia no vende. Como en el <b>yin-yang</b>, cada una lleva un poco de la otra."],
 ["04","En el centro, <em>改善</em>","Lo que las mantiene unidas es el <b>kaizen</b>, la mejora continua: probar, medir, aprender y volver a empezar un poco mejor que antes."],
 ["05","Así nace <em>MARK KAIZEN</em>","Una marca que no busca ser perfecta, sino <b>evolucionar</b>. Estrategia y creatividad en equilibrio, mejorando con cada proyecto."]];
el.innerHTML=`<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<clipPath id="ogL" clipPathUnits="objectBoundingBox"><path d="M.5,0 A.5,.5 0 0 0 .5,1 A.25,.25 0 0 0 .5,.5 A.25,.25 0 0 1 .5,0 Z"/></clipPath>
<clipPath id="ogR" clipPathUnits="objectBoundingBox"><path d="M.5,0 A.5,.5 0 0 1 .5,1 A.25,.25 0 0 0 .5,.5 A.25,.25 0 0 1 .5,0 Z"/></clipPath></defs></svg>
<div class="og-stick"><div class="og-bg"></div>
 <div class="og-stage" aria-hidden="true">
  <div class="pc dr"><img src="img/simbolo.webp" alt=""></div><div class="pc ct"><img src="img/simbolo.webp" alt=""></div>
  <span class="lbl l">Estrategia</span><span class="lbl r">Creatividad</span><span class="kj"></span>
  <svg class="ring" viewBox="0 0 200 200"><circle cx="100" cy="100" r="95"/></svg>
  <div class="og-word"><b>MARK <i>KAIZEN</i></b><small>MEJORA CONTINUA</small></div>
 </div>
 <div class="og-txt"><p class="og-eb">Cómo nació la marca</p>${S.map((s,i)=>`<div class="og-step" data-i="${i}"><span class="n">${s[0]} / 05</span><h3>${s[1]}</h3><p>${s[2]}</p></div>`).join("")}<div class="og-dots" aria-hidden="true">${S.map(()=>"<i></i>").join("")}</div></div>
</div>`;
const steps=[...el.querySelectorAll(".og-step")],dots=[...el.querySelectorAll(".og-dots i")];
const cl=(x,a,b)=>Math.min(1,Math.max(0,(x-a)/(b-a)));
const ease=t=>1-Math.pow(1-t,3);
function set(p){
 const v={a:ease(cl(p,.02,.18)),b:ease(cl(p,.2,.36)),c:ease(cl(p,.42,.6)),d:ease(cl(p,.62,.76)),e:ease(cl(p,.8,.94))};
 for(const k in v)el.style.setProperty("--"+k,v[k].toFixed(4));
 const i=p<.2?0:p<.4?1:p<.61?2:p<.79?3:4;
 steps.forEach((s,j)=>s.classList.toggle("on",j==i));dots.forEach((d,j)=>d.classList.toggle("on",j==i));
}
if(matchMedia("(prefers-reduced-motion: reduce)").matches){set(1);steps.forEach(s=>s.classList.add("on"));return}
let tk=0;function upd(){tk=0;const r=el.getBoundingClientRect(),h=r.height-innerHeight;set(h>0?Math.min(1,Math.max(0,-r.top/h)):1)}
addEventListener("scroll",()=>{if(!tk)tk=requestAnimationFrame(upd)},{passive:true});addEventListener("resize",upd);upd();
})();
