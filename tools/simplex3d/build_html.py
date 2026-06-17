"""
build_html.py -- assemble the self-contained interactive page.

Injects the verified step data (steps.json) into an HTML template that renders
the 3D polytope with Plotly and the per-step mathematics with KaTeX.  The data
is embedded inline, so the resulting file works both by double-clicking it
locally (file://) and when served from GitHub Pages.

Usage:  python3 build_html.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "steps.json")))
OUT = os.path.join(HERE, "..", "..", "docs", "simplex3d", "index.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Simplex on a Convex Polytope in &#8477;&#179; &middot; OM 600</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
      integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" crossorigin="anonymous">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
        integrity="sha384-7zkQWkzuo3B5mTepMUcHkMB5jZaolc2xDwL6VFqjFALcbeS9Ggm/Yr2r3Dy4lfFg" crossorigin="anonymous"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
        integrity="sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk" crossorigin="anonymous"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root{
    --bg:#0d1326; --panel:#121a33; --panel2:#16203d; --edge:#2e4a72;
    --txt:#e8eef9; --mute:#8fa2c4; --gold:#ffd23f; --glow:#ff8c42;
    --red:#ff3b6b; --obj:#36e0a4; --blue:#3b6fb6;
  }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg);color:var(--txt);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  a{color:var(--obj)}
  header{padding:22px 26px 10px;text-align:center;border-bottom:1px solid var(--edge)}
  header h1{margin:0 0 6px;font-size:23px;font-weight:700;letter-spacing:.2px}
  header .lp{color:var(--mute);font-size:15px;margin:8px 0 2px}
  header .lp .katex{color:var(--txt)}
  .sub{color:var(--mute);font-size:12.5px;margin-top:6px}
  .wrap{display:grid;grid-template-columns:1.18fr .82fr;gap:18px;
    max-width:1280px;margin:16px auto;padding:0 18px}
  @media(max-width:940px){.wrap{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--edge);border-radius:14px;overflow:hidden}
  #plot{width:100%;height:560px}
  @media(max-width:940px){#plot{height:440px}}
  .legend{display:flex;flex-wrap:wrap;gap:14px;padding:10px 16px;border-top:1px solid var(--edge);
    font-size:12.5px;color:var(--mute);align-items:center}
  .legend i{display:inline-block;width:13px;height:13px;border-radius:3px;margin-right:6px;vertical-align:-2px}
  .math{padding:18px 20px 6px;min-height:540px}
  .steptitle{margin:2px 0 14px;font-size:13px;color:var(--mute);display:flex;align-items:center;gap:10px}
  .pill{background:var(--panel2);border:1px solid var(--edge);border-radius:999px;
    padding:3px 11px;font-size:12px;color:var(--gold);font-weight:600}
  .pill.opt{color:var(--obj)}
  #title .katex{font-size:1.02em}
  .block{background:var(--panel2);border:1px solid var(--edge);border-left:3px solid var(--blue);
    border-radius:10px;padding:11px 14px;margin:10px 0;opacity:0;
    animation:rise .5s ease forwards}
  .block .blabel{font-size:12.5px;color:var(--mute);margin-bottom:7px;font-weight:600}
  .block .bbody{overflow-x:auto;overflow-y:hidden}
  .block.enter{border-left-color:var(--gold)}
  .block.ratio{border-left-color:var(--glow)}
  .block.opt{border-left-color:var(--obj)}
  @keyframes rise{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}
  .narr{color:var(--mute);font-size:13px;line-height:1.6;margin:14px 4px 4px;font-style:italic}
  .controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center;
    padding:14px;margin:4px auto 26px;max-width:1280px}
  button{background:var(--panel2);color:var(--txt);border:1px solid var(--edge);
    border-radius:9px;padding:9px 15px;font-size:14px;cursor:pointer;transition:.15s}
  button:hover{border-color:var(--obj);color:var(--obj)}
  button.primary{background:var(--obj);color:#06241a;border-color:var(--obj);font-weight:700}
  button:disabled{opacity:.4;cursor:not-allowed}
  .toggle{display:flex;align-items:center;gap:7px;color:var(--mute);font-size:13px}
  .ind{color:var(--mute);font-size:13px;min-width:96px;text-align:center}
  input[type=range]{accent-color:var(--obj)}
  footer{color:var(--mute);font-size:12px;text-align:center;padding:0 20px 34px;line-height:1.6}
</style>
</head>
<body>
<header>
  <h1>The Simplex Algorithm Traversing a Convex Polytope in &#8477;&#179;</h1>
  <div class="lp" id="lp-obj"></div>
  <div class="lp" id="lp-con"></div>
  <div class="sub">OM&nbsp;600 &middot; Linear Programming &mdash; decomposition / feasible-direction method.
     The algorithm walks vertex&#8209;to&#8209;vertex along edges of the feasible region, improving
     <span id="zinline"></span> at each pivot until no improving direction remains.</div>
</header>

<div class="wrap">
  <div class="card">
    <div id="plot"></div>
    <div class="legend">
      <span><i style="background:#3b6fb6"></i>feasible polytope $\{x\ge0,\,Ax\le b\}$</span>
      <span><i style="background:#7f93b8"></i>extreme points (BFS)</span>
      <span><i style="background:#ffd23f"></i>simplex path</span>
      <span><i style="background:#ff3b6b"></i>current vertex</span>
      <span><i style="background:#36e0a4"></i>$\nabla z=c$</span>
    </div>
  </div>
  <div class="card math">
    <div class="steptitle"><span class="pill" id="pill"></span><span id="ind2"></span></div>
    <div id="title"></div>
    <div id="blocks"></div>
    <div class="narr" id="narr"></div>
  </div>
</div>

<div class="controls">
  <button id="reset">&#8634; Reset</button>
  <button id="prev">&#9664; Prev</button>
  <button id="play" class="primary">&#9654; Play</button>
  <button id="next">Next &#9654;</button>
  <span class="ind" id="ind"></span>
  <label class="toggle">Speed
    <input type="range" id="speed" min="0.5" max="2.5" step="0.1" value="1.1"></label>
  <label class="toggle"><input type="checkbox" id="rot" checked> auto&#8209;rotate</label>
</div>

<footer>
  Exact rational arithmetic throughout (no floating&#8209;point round&#8209;off).
  Reduced cost&nbsp;$\bar c_j=c_j-c_B^{\top}B^{-1}A_j=\langle c,v^j\rangle$;
  direction&nbsp;$v^s=[-B^{-1}A_s;\,e_s]$;
  ratio test&nbsp;$\lambda^*=\min_{i:\,\bar a_{is}>0}\bar b_i/\bar a_{is}$;
  update&nbsp;$x^{\text{new}}=x^{\text{old}}+\lambda^*v^s$.
  <br>Generated from the OM&nbsp;600 course notes &middot; rendered with Plotly + KaTeX.
</footer>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const V = DATA.geometry.vertices, FACES = DATA.geometry.faces,
      EDGES = DATA.geometry.edges, C = DATA.geometry.objective,
      STEPS = DATA.steps, PATH = DATA.path_pts;
const col = (arr,i)=>arr.map(p=>p[i]);

// ---- triangulate faces for mesh3d -------------------------------------- //
let mi=[],mj=[],mk=[];
FACES.forEach(f=>{for(let t=1;t<f.length-1;t++){mi.push(f[0]);mj.push(f[t]);mk.push(f[t+1]);}});
// ---- edge segments (nulls separate disjoint segments) ------------------ //
let ex=[],ey=[],ez=[];
EDGES.forEach(([a,b])=>{ex.push(V[a][0],V[b][0],null);ey.push(V[a][1],V[b][1],null);ez.push(V[a][2],V[b][2],null);});
// ---- objective arrow (cone) at the centroid ---------------------------- //
const cen=[2,2,2], cn=Math.hypot(C[0],C[1],C[2]), cs=2.2;
const objVec=[C[0]/cn*cs, C[1]/cn*cs, C[2]/cn*cs];

const T = {                       // trace indices
  MESH:0, EDGES:1, VERTS:2, OBJ:3, PATH:4, VISITED:5, CURSOR:6
};
function traces(){
  return [
    {type:'mesh3d', x:col(V,0),y:col(V,1),z:col(V,2), i:mi,j:mj,k:mk,
     color:'#3b6fb6', opacity:0.14, flatshading:true, hoverinfo:'skip',
     lighting:{ambient:0.85,diffuse:0.4,specular:0.05}, name:'polytope'},
    {type:'scatter3d', mode:'lines', x:ex,y:ey,z:ez,
     line:{color:'#9fb6d6',width:3}, opacity:0.55, hoverinfo:'skip'},
    {type:'scatter3d', mode:'markers', x:col(V,0),y:col(V,1),z:col(V,2),
     marker:{size:4.2,color:'#7f93b8',line:{color:'#fff',width:0.5}},
     hovertemplate:'extreme point (%{x},%{y},%{z})<extra></extra>', name:'BFS'},
    {type:'cone', x:[cen[0]],y:[cen[1]],z:[cen[2]], u:[objVec[0]],v:[objVec[1]],w:[objVec[2]],
     sizemode:'absolute', sizeref:1.1, anchor:'tail', showscale:false,
     colorscale:[[0,'#36e0a4'],[1,'#36e0a4']], hoverinfo:'skip'},
    {type:'scatter3d', mode:'lines', x:[PATH[0][0]],y:[PATH[0][1]],z:[PATH[0][2]],
     line:{color:'#ffd23f',width:9}, hoverinfo:'skip'},
    {type:'scatter3d', mode:'markers', x:[PATH[0][0]],y:[PATH[0][1]],z:[PATH[0][2]],
     marker:{size:7,color:'#ffd23f',line:{color:'#fff',width:1}}, hoverinfo:'skip'},
    {type:'scatter3d', mode:'markers', x:[PATH[0][0]],y:[PATH[0][1]],z:[PATH[0][2]],
     marker:{size:12,color:'#ff3b6b',line:{color:'#fff',width:1.5}},
     hovertemplate:'current vertex<extra></extra>'}
  ];
}
const axis={showbackground:true,backgroundcolor:'#0d1326',gridcolor:'rgba(255,255,255,0.08)',
  zerolinecolor:'rgba(255,255,255,0.18)',color:'#8fa2c4',
  range:[0,4.4],tickvals:[0,2,4]};
const layout={paper_bgcolor:'#0d1326',plot_bgcolor:'#0d1326',showlegend:false,
  margin:{l:0,r:0,t:0,b:0},
  scene:{xaxis:{...axis,title:{text:'x₁'}},yaxis:{...axis,title:{text:'x₂'}},
         zaxis:{...axis,title:{text:'x₃'}},aspectmode:'cube',
         camera:{eye:{x:1.55,y:1.55,z:1.15}}}};
const gd=document.getElementById('plot');
Plotly.newPlot(gd, traces(), layout, {displayModeBar:false, responsive:true});

// ----------------------------- state ------------------------------------ //
let cur=0, playing=false, glideRAF=null, playTimer=null;
const speed=()=>parseFloat(document.getElementById('speed').value);
const easeIO=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;

function setPlot(k, cursorPt){
  const line=PATH.slice(0,k+1).concat(cursorPt?[cursorPt]:[]);
  const vis=PATH.slice(0,k+1);
  const cp=cursorPt||PATH[k];
  Plotly.restyle(gd,{x:[col(line,0)],y:[col(line,1)],z:[col(line,2)]},[T.PATH]);
  Plotly.restyle(gd,{x:[col(vis,0)],y:[col(vis,1)],z:[col(vis,2)]},[T.VISITED]);
  Plotly.restyle(gd,{x:[[cp[0]]],y:[[cp[1]]],z:[[cp[2]]]},[T.CURSOR]);
}

function renderMath(k){
  const s=STEPS[k];
  const pill=document.getElementById('pill');
  pill.textContent = s.status==='optimal' ? 'OPTIMAL' : ('PIVOT '+s.iter);
  pill.className = 'pill'+(s.status==='optimal'?' opt':'');
  document.getElementById('ind2').textContent =
     'vertex x = ('+s.point.join(', ')+'),  z = '+s.z;
  const tEl=document.getElementById('title'); tEl.innerHTML='';
  katex.render(s.title, tEl, {displayMode:true, throwOnError:false});
  const host=document.getElementById('blocks'); host.innerHTML='';
  s.blocks.forEach((blk,bi)=>{
    const card=document.createElement('div'); card.className='block';
    if(/Entering/.test(blk.label)) card.classList.add('enter');
    if(/ratio/i.test(blk.label))  card.classList.add('ratio');
    if(/Certificate|Dual|Optimality/.test(blk.label)&&s.status==='optimal') card.classList.add('opt');
    card.style.animationDelay=(bi*0.10)+'s';
    const lab=document.createElement('div'); lab.className='blabel'; lab.innerHTML=blk.label;
    renderMathInElement(lab,{delimiters:[{left:'$',right:'$',display:false}],throwOnError:false});
    const body=document.createElement('div'); body.className='bbody';
    katex.render(blk.tex, body, {displayMode:true, throwOnError:false});
    card.appendChild(lab); card.appendChild(body); host.appendChild(card);
  });
  document.getElementById('narr').textContent=s.narr||s.narrative||'';
  document.getElementById('ind').textContent='Step '+(k+1)+' / '+STEPS.length;
  document.getElementById('prev').disabled=(k===0);
  document.getElementById('next').disabled=(k===STEPS.length-1);
}

function showStep(k){ cur=k; setPlot(k); renderMath(k); }

function glideTo(target, cb){
  if(glideRAF) cancelAnimationFrame(glideRAF);
  const from=cur, p0=PATH[from], p1=PATH[target];
  const dur=Math.max(220, 850/speed());
  let t0=null;
  function frame(ts){
    if(t0===null) t0=ts;
    const t=Math.min(1,(ts-t0)/dur), e=easeIO(t);
    const cp=[p0[0]+(p1[0]-p0[0])*e, p0[1]+(p1[1]-p0[1])*e, p0[2]+(p1[2]-p0[2])*e];
    setPlot(from, cp);
    if(t<1){ glideRAF=requestAnimationFrame(frame); }
    else { showStep(target); if(cb) cb(); }
  }
  glideRAF=requestAnimationFrame(frame);
}

function next(){ if(cur<STEPS.length-1) glideTo(cur+1); }
function prev(){ if(cur>0) glideTo(cur-1); }

function play(){
  playing=true; document.getElementById('play').innerHTML='&#10073;&#10073; Pause';
  const tick=()=>{
    if(!playing) return;
    if(cur>=STEPS.length-1){ stop(); return; }
    glideTo(cur+1, ()=>{ playTimer=setTimeout(tick, 1500/speed()); });
  };
  if(cur>=STEPS.length-1) showStep(0);
  tick();
}
function stop(){ playing=false; clearTimeout(playTimer);
  document.getElementById('play').innerHTML='&#9654; Play'; }

document.getElementById('play').onclick =()=> playing?stop():play();
document.getElementById('next').onclick =()=>{stop();next();};
document.getElementById('prev').onclick =()=>{stop();prev();};
document.getElementById('reset').onclick=()=>{stop();showStep(0);};

// ----------------------- gentle auto-rotation --------------------------- //
let theta=Math.atan2(1.55,1.55), R=Math.hypot(1.55,1.55), zEye=1.15;
setInterval(()=>{
  if(!document.getElementById('rot').checked) return;
  theta+=0.0045;
  Plotly.relayout(gd,{'scene.camera.eye':{x:R*Math.cos(theta),y:R*Math.sin(theta),z:zEye}});
},60);

// ------------------------------ boot ------------------------------------ //
function boot(){
  katex.render(DATA.lp.objective_tex, document.getElementById('lp-obj'),
               {displayMode:false, throwOnError:false});
  const con=DATA.lp.constraints_tex.map(c=>'\\;'+c+'\\;').join(',\\quad ');
  katex.render('\\text{s.t.}\\quad '+con, document.getElementById('lp-con'),
               {displayMode:false, throwOnError:false});
  katex.render('z=c^{\\top}x', document.getElementById('zinline'),
               {displayMode:false, throwOnError:false});
  renderMathInElement(document.querySelector('.legend'),
               {delimiters:[{left:'$',right:'$',display:false}],throwOnError:false});
  renderMathInElement(document.querySelector('footer'),
               {delimiters:[{left:'$',right:'$',display:false}],throwOnError:false});
  showStep(0);
}
window.addEventListener('load', ()=>{ // wait until KaTeX (deferred) is ready
  const wait=setInterval(()=>{ if(window.katex&&window.renderMathInElement){clearInterval(wait);boot();} },30);
});
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__DATA__", json.dumps(DATA))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write(html)
print("wrote", os.path.normpath(OUT), f"({len(html)/1024:.0f} KB)")
