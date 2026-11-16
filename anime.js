/* MARK KAIZEN · capa anime (index.html y marca.html).
   Opening, paneles de manga, barrido de pincel, botón yin-yang, inclinación de tarjetas y pausa fuera de pantalla.
   Solo mueve transform y opacity. Con prefers-reduced-motion deja todo quieto y visible. */
(()=>{
const D=document,R=D.documentElement;
const RM=matchMedia("(prefers-reduced-motion: reduce)").matches;
const el=(tag,cls,html)=>{const e=D.createElement(tag);if(cls)e.className=cls;if(html)e.innerHTML=html;return e};

/* ---------- 1 · Opening: las dos mitades del símbolo se unen (máx. 2 s, se puede saltar) ---------- */
const op=D.getElementById("op");let opT=0;
function opEnd(){clearTimeout(opT);R.classList.remove("op-run");if(op){op.classList.remove("skip");op.hidden=true}}
function opSkip(){if(!R.classList.contains("op-run"))return;clearTimeout(opT);op.classList.add("skip");opT=setTimeout(opEnd,190)}
function opStart(){opT=setTimeout(opEnd,2000)}
if(op){
 op.addEventListener("click",opSkip);
 addEventListener("keydown",opSkip);
 if(R.classList.contains("op-run"))opStart();else op.hidden=true;
}
/* para volver a verlo desde el manual de marca */
window.MKOpening={play(){if(!op||RM)return;opEnd();op.hidden=false;void op.offsetWidth;R.classList.add("op-run");opStart()}};
D.querySelectorAll("[data-opening]").forEach(b=>b.addEventListener("click",()=>window.MKOpening.play()));

/* ---------- 2 · Cada sección entra como panel de manga ---------- */
const NUM=["一","二","三","四","五","六","七","八","九","十","十一","十二","十三","十四"];
const mio=RM?null:new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("mg-in");mio.unobserve(e.target)}}),{rootMargin:"0px 0px -16% 0px"});
D.querySelectorAll("[data-ch]").forEach(sec=>{
 const w=sec.querySelector(".w")||sec,n=sec.dataset.ch,k=sec.dataset.kanji||"",own=!!sec.querySelector(".sh .num");
 w.classList.add("mgp");
 const mg=el("div","mg"+(own?" has-num":""),`<i class="mg-cut"></i><i class="mg-d"></i>${own?"":`<b class="mg-n">${n}</b>`}<span class="mg-k" lang="ja">${k}</span><span class="mg-v" lang="ja">第${NUM[+n-1]||n}話</span>`);
 mg.setAttribute("aria-hidden","true");w.prepend(mg);
 if(RM){sec.classList.add("mg-in");return}
 const wp=el("i","mg-wipe");wp.setAttribute("aria-hidden","true");w.append(wp);
 wp.addEventListener("transitionend",()=>wp.remove());
 mio.observe(sec);
});

/* ---------- 3 · Barrido de pincel naranja al navegar desde el menú ---------- */
let brush=null,busy=false;
function jump(t,id){
 const sb=R.style.scrollBehavior;R.style.scrollBehavior="auto";
 t.scrollIntoView({block:"start"});R.style.scrollBehavior=sb;
 try{history.pushState(null,"","#"+id)}catch(e){}
 if(!t.hasAttribute("tabindex"))t.setAttribute("tabindex","-1");t.focus({preventScroll:true});
}
D.addEventListener("click",e=>{
 const a=e.target.closest&&e.target.closest('a[href^="#"]');
 if(!a||e.metaKey||e.ctrlKey||e.shiftKey||!a.closest("nav,.drawer"))return;
 const id=a.getAttribute("href").slice(1),t=id&&D.getElementById(id);if(!t)return;
 e.preventDefault();
 if(RM){jump(t,id);return}
 if(busy)return;busy=true;
 if(!brush){brush=el("div","brush");brush.setAttribute("aria-hidden","true");D.body.append(brush)}
 brush.classList.remove("go");void brush.offsetWidth;brush.classList.add("go");
 setTimeout(()=>jump(t,id),340);
 setTimeout(()=>{brush.classList.remove("go");busy=false},760);
});

/* ---------- 4 · Botón fijo yin-yang: gira con el scroll, anillo de progreso, vuelve arriba ---------- */
const yy=el("button","yyb",'<span class="yyr" aria-hidden="true"><i class="a"><b></b></i><i class="b"><b></b></i></span><img src="img/simbolo.webp" alt="" width="42" height="42">');
yy.type="button";yy.setAttribute("aria-label","Volver arriba");D.body.append(yy);
const yi=yy.querySelector("img"),ya=yy.querySelector(".a b"),yb=yy.querySelector(".b b");
yy.addEventListener("click",()=>scrollTo({top:0,behavior:RM?"auto":"smooth"}));
let tk=0;
function onScroll(){tk=0;const h=R.scrollHeight-innerHeight,p=h>0?Math.min(1,Math.max(0,scrollY/h)):0;
 yy.classList.toggle("on",scrollY>260);
 ya.style.transform=`rotate(${Math.min(p,.5)*360}deg)`;
 yb.style.transform=`rotate(${Math.max(p-.5,0)*360}deg)`;
 if(!RM)yi.style.transform=`rotate(${(p*1080).toFixed(1)}deg)`;
}
addEventListener("scroll",()=>{if(!tk)tk=requestAnimationFrame(onScroll)},{passive:true});
addEventListener("resize",onScroll);onScroll();

/* ---------- 5 · Leve inclinación de las tarjetas (solo con mouse) ---------- */
const TILT=".sv,.met,.edu>div,.cl,.card,.app,.mean,.vq blockquote,.vcard";
if(!RM&&matchMedia("(hover:hover) and (pointer:fine)").matches){
 let cur=null;
 /* las tarjetas que entran con animación la sueltan al terminar, para poder inclinarse */
 D.addEventListener("animationend",e=>{const t=e.target;if(t.classList&&t.classList.contains("ain")&&t.matches(TILT))t.classList.remove("ain")});
 D.addEventListener("pointermove",e=>{
  const c=e.target.closest?e.target.closest(TILT):null;
  if(cur&&cur!==c){cur.style.transform="";cur=null}
  if(!c||c.classList.contains("ain"))return;cur=c;
  const r=c.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
  c.style.transform=`perspective(900px) rotateX(${(-y*5).toFixed(2)}deg) rotateY(${(x*6).toFixed(2)}deg) translateY(-4px)`;
 },{passive:true});
 D.addEventListener("pointerleave",()=>{if(cur){cur.style.transform="";cur=null}});
}

/* ---------- 6 · Pausa lo que no está en pantalla ---------- */
if("IntersectionObserver" in window){
 const pio=new IntersectionObserver(es=>es.forEach(e=>e.target.classList.toggle("offs",!e.isIntersecting)),{rootMargin:"80px"});
 const seen=new WeakSet();
 const scan=()=>{if(!D.getAnimations)return;D.getAnimations().forEach(a=>{
  const f=a.effect,t=f&&f.target;if(!t||seen.has(t)||!f.getTiming||f.getTiming().iterations!==Infinity)return;
  if(getComputedStyle(t).position==="fixed")return;seen.add(t);pio.observe(t)})};
 addEventListener("load",()=>{scan();setTimeout(scan,2600)});
 /* los videos de la marca se detienen al salir de pantalla */
 const vio=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting&&!e.target.paused)e.target.pause()}));
 D.querySelectorAll(".vcard video").forEach(v=>vio.observe(v));
 /* trazo de las tarjetas de video al entrar */
 const cio=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("in");cio.unobserve(e.target)}}),{threshold:.3});
 D.querySelectorAll(".vcard").forEach(c=>cio.observe(c));
}
})();
