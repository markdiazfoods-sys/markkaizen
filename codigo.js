/* MARK KAIZEN · 第八話 開発 · ciclo Kaizen (Planear · Hacer · Verificar · Actuar).
   Recorre los 4 pasos solo mientras la sección está en pantalla; tocar un paso lo fija.
   Con prefers-reduced-motion no hay recorrido automático: todo queda visible y quieto. */
(()=>{
const sec=document.getElementById("cd");if(!sec)return;
const RM=matchMedia("(prefers-reduced-motion: reduce)").matches;
const btns=[...sec.querySelectorAll(".cd-st button")],qs=[...sec.querySelectorAll(".cd-ring .q")];
let k=-1,t=0,pinned=false;

function set(i){
 k=i;sec.dataset.k=i;
 btns.forEach((b,j)=>b.setAttribute("aria-pressed",String(j===i)));
 qs.forEach((q,j)=>q.classList.toggle("on",j===i));
}
function stop(){clearInterval(t);t=0}
function start(){if(RM||pinned||t)return;sec.classList.add("cyc");if(k<0)set(0);t=setInterval(()=>set((k+1)%4),2400)}
function pin(i){pinned=true;stop();sec.classList.add("cyc");set(i)}

btns.forEach((b,i)=>b.addEventListener("click",()=>pin(i)));
qs.forEach((q,i)=>q.addEventListener("click",()=>pin(i)));

if(RM){sec.classList.add("in");set(0);return}
new IntersectionObserver(es=>es.forEach(e=>{
 if(e.isIntersecting){sec.classList.add("in","on");start()}
 else{sec.classList.remove("on");stop()}
}),{threshold:.25}).observe(sec);
})();
