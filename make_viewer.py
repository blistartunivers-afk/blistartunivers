html = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evolución CPPN</title>
<style>
:root{--bg:#0a0e14;--bg-raised:#0f141c;--line:#232b38;--ink:#e9e7e1;--ink-dim:#8b93a3;--signal:#5eead4;--amber:#f5a623;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:monospace;line-height:1.5}
.wrap{max-width:1200px;margin:0 auto;padding:20px}
h1{font-size:28px;margin-bottom:8px}
.controls{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.btn{background:var(--bg-raised);border:1px solid var(--line);color:var(--ink);padding:10px 16px;border-radius:6px;cursor:pointer}
.btn.primary{background:var(--signal);color:var(--bg);border-color:var(--signal)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.stat{background:var(--bg-raised);border:1px solid var(--line);padding:16px;border-radius:8px}
.stat-value{font-size:24px;font-weight:700;color:var(--signal)}
.main-grid{display:grid;grid-template-columns:1fr 420px;gap:20px}
@media(max-width:900px){.main-grid{grid-template-columns:1fr}}
.panel{background:var(--bg-raised);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.panel-header{padding:16px;border-bottom:1px solid var(--line)}
canvas{width:100%;height:100%;display:block}
.population-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:8px;padding:16px;max-height:400px;overflow:auto}
.individual{background:var(--bg);border:1px solid var(--line);border-radius:6px;overflow:hidden}
.individual canvas{width:100%;height:80px}
</style>
</head>
<body>
<div class="wrap">
<h1>Evolución CPPN</h1>
<div class="controls">
<button class="btn primary" id="btnStart">Start</button>
<button class="btn" id="btnPause" disabled>Pause</button>
<button class="btn" id="btnStep" disabled>Step</button>
<button class="btn" id="btnReset">Reset</button>
</div>
<div class="stats">
<div class="stat"><div>Gen</div><div class="stat-value" id="statGen">0</div></div>
<div class="stat"><div>Best Fit</div><div class="stat-value" id="statBestFit">0</div></div>
<div class="stat"><div>Avg Fit</div><div class="stat-value" id="statAvgFit">0</div></div>
</div>
<div class="main-grid">
<div class="panel"><div class="panel-header"><h2>Best Individual</h2></div><canvas id="bestCanvas" width="256" height="256"></canvas></div>
<div><div class="panel"><div class="panel-header"><h2>Fitness Chart</h2></div><canvas id="fitnessChart"></canvas></div>
<div class="panel"><div class="panel-header"><h2>Population</h2></div><div class="population-grid" id="populationGrid"></div></div></div>
</div>
</div>
<script>
const ACT={sin:Math.sin,cos:Math.cos,tanh:Math.tanh,gauss:v=>Math.exp(-v*v),softsign:v=>v/(1+Math.abs(v))};
function evalCPPN(g,w=64,h=64){const w1=g.w1,a1=g.act1.map(n=>ACT[n]),w2=g.w2,a2=g.act2.map(n=>ACT[n]),w3=g.w3,I=new Float32Array(w*h);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const nx=(x/w)*2-1,ny=(y/h)*2-1,r=Math.hypot(nx,ny),inp=[nx,ny,r,1];
const h1=[],h2=[];for(let ni=0;ni<8;ni++){let s=0;for(let k=0;k<4;k++)s+=inp[k]*w1[ni][k];h1[ni]=a1[ni](s);}
for(let ni=0;ni<8;ni++){let s=0;for(let k=0;k<8;k++)s+=h1[k]*w2[ni][k];h2[ni]=a2[ni](s);}
let out=0;for(let k=0;k<8;k++)out+=h2[k]*w3[k];I[y*w+x]=(Math.tanh(out)+1)/2;}return I;}
function metrics(I,w,h){const t=w*h,f=Array.from(I),H=new Uint32Array(256);f.forEach(v=>H[Math.min(255,Math.floor(v*255))]++);
let sh=0;H.forEach(c=>{if(c>0){const p=c/t;sh-=p*Math.log2(p);}});
let sp=0,sc=0;for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){const dx=I[y*w+x+1]-I[y*w+x-1],dy=I[(y+1)*w+x]-I[(y-1)*w+x];sp+=Math.hypot(dx,dy);sc++;}
const spatial=sc?sp/sc:0;const mean=f.reduce((a,b)=>a+b,0)/t;
const contrast=Math.sqrt(f.reduce((a,b)=>a+(b-mean)**2,0)/t);
const uniq=new Set(f.map(v=>Math.min(255,Math.floor(v*255)))).size;
const div=uniq/256;let ss=0,sc2=0;for(let y=0;y<h;y++)for(let x=0;x<w/2;x++){ss+=Math.abs(I[y*w+x]-I[y*w+w-1-x]);sc2++;}
const sym=sc2?1-ss/sc2:1;return{shannon:sh,spatial,contrast,diversity:div,symmetry:sym,unique:uniq};}
function fitness(m){const n={shannon:Math.min(m.shannon/8,1),spatial:Math.min(m.spatial/2,1),contrast:Math.min(m.contrast/0.5,1),diversity:m.diversity,symmetry:m.symmetry};
return 0.3*n.shannon+0.25*n.spatial+0.2*n.contrast+0.15*n.diversity+0.1*n.symmetry;}
function evalGenome(g){const I=evalCPPN(g);const m=metrics(I,64,64);return{fitness:fitness(m),metrics:m,intensity:I};}
const ACTN=['sin','cos','tanh','gauss','softsign'];
function mulberry32(a){return()=>{a=(a+0x6D2B79F5)|0;let t=Math.imul(a^(a>>>15),1|a);t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296;};}
function randGenome(seed){const r=seed?mulberry32(seed):Math.random;return{version:2,seed,architecture:[4,8,8,1],w1:Array(8).fill().map(()=>Array(4).fill().map(()=>r()*4-2)),act1:Array(8).fill().map(()=>ACTN[Math.floor(r()*5)]),w2:Array(8).fill().map(()=>Array(8).fill().map(()=>r()*4-2)),act2:Array(8).fill().map(()=>ACTN[Math.floor(r()*5)]),w3:Array(8).fill().map(()=>r()*4-2),generation:0,fitness:null,metrics:{},parent_ids:[]};}
function mutate(g,rate=0.15,scale=0.3){const m=JSON.parse(JSON.stringify(g));m.generation=g.generation+1;m.fitness=null;m.metrics={};m.parent_ids=[g.id||'u'];
for(let i=0;i<m.w1.length;i++){for(let j=0;j<m.w1[i].length;j++)if(Math.random()<rate){m.w1[i][j]+=(Math.random()*2-1)*scale;m.w1[i][j]=Math.max(-3,Math.min(3,m.w1[i][j]));}if(Math.random()<rate*0.5)m.act1[i]=ACTN[Math.floor(Math.random()*5)];}
for(let i=0;i<m.w2.length;i++){for(let j=0;j<m.w2[i].length;j++)if(Math.random()<rate){m.w2[i][j]+=(Math.random()*2-1)*scale;m.w2[i][j]=Math.max(-3,Math.min(3,m.w2[i][j]));}if(Math.random()<rate*0.5)m.act2[i]=ACTN[Math.floor(Math.random()*5)];}
for(let i=0;i<m.w3.length;i++)if(Math.random()<rate){m.w3[i]+=(Math.random()*2-1)*scale;m.w3[i]=Math.max(-3,Math.min(3,m.w3[i]));}
return m;}
function crossover(a,b){const c=JSON.parse(JSON.stringify(a));c.generation=Math.max(a.generation,b.generation)+1;c.fitness=null;c.metrics={};c.parent_ids=[a.id||'a',b.id||'b'];
for(let i=0;i<c.w1.length;i++){for(let j=0;j<c.w1[i].length;j++)if(Math.random()<0.5)c.w1[i][j]=b.w1[i][j];if(Math.random()<0.5)c.act1[i]=b.act1[i];}
for(let i=0;i<c.w2.length;i++){for(let j=0;j<c.w2[i].length;j++)if(Math.random()<0.5)c.w2[i][j]=b.w2[i][j];if(Math.random()<0.5)c.act2[i]=b.act2[i];}
for(let i=0;i<c.w3.length;i++)if(Math.random()<0.5)c.w3[i]=b.w3[i];
return c;}

let pop=[],running=false,gen=0,animId;
const canvas=document.getElementById('bestCanvas'),ctx=canvas.getContext('2d');
const chart=document.getElementById('fitnessChart'),cctx=chart.getContext('2d');
const popGrid=document.getElementById('populationGrid');
function renderBest(ind){const I=ind.intensity||evalCPPN(ind.genome,256,256);const img=ctx.createImageData(256,256);
for(let i=0;i<I.length;i++){const v=Math.floor(I[i]*255);img.data[i*4]=v;img.data[i*4+1]=v;img.data[i*4+2]=v;img.data[i*4+3]=255;}
ctx.putImageData(img,0,0);
document.getElementById('statGen').textContent=gen;
document.getElementById('statBestFit').textContent=ind.fitness.toFixed(4);
document.getElementById('statAvgFit').textContent=(pop.reduce((a,b)=>a+b.fitness,0)/pop.length).toFixed(4);
}
function renderPop(){popGrid.innerHTML='';pop.forEach((ind,i)=>{const div=document.createElement('div');div.className='individual'+(i<2?' elite':'');
const c=document.createElement('canvas');c.width=80;c.height=80;const cx=c.getContext('2d');
const I=ind.intensity||evalCPPN(ind.genome,80,80);const img=cx.createImageData(80,80);
for(let k=0;k<I.length;k++){const v=Math.floor(I[k]*255);img.data[k*4]=v;img.data[k*4+1]=v;img.data[k*4+2]=v;img.data[k*4+3]=255;}
cx.putImageData(img,0,0);div.appendChild(c);
const info=document.createElement('div');info.style.padding='4px';info.style.fontSize='10px';
info.innerHTML='<span style="color:#5eead4">'+ind.fitness.toFixed(3)+'</span> gen'+ind.genome.generation;
div.appendChild(info);popGrid.appendChild(div);});}
function step(){if(pop.length===0)return;
pop.sort((a,b)=>b.fitness-a.fitness);
renderBest(pop[0]);renderPop();
const elite=pop.slice(0,2).map(x=>JSON.parse(JSON.stringify(x.genome)));
const newPop=elite.map((g,i)=>{g.id='gen'+g.generation+'_elite_'+i;return g;});
while(newPop.length<pop.length){const p1=pop[Math.floor(Math.random()*3)],p2=pop[Math.floor(Math.random()*3)];
let child=Math.random()<0.7?crossover(p1.genome,p2.genome):JSON.parse(JSON.stringify(p1.genome));
child=mutate(child,0.15);child.id='gen'+child.generation+'_'+newPop.length;newPop.push(child);}
pop=newPop.map(g=>{const r=evalGenome(g);return{genome:g,fitness:r.fitness,metrics:r.metrics,intensity:r.intensity};});
gen++;}
function loop(){if(!running)return;step();animId=requestAnimationFrame(loop);}
document.getElementById('btnStart').onclick=()=>{if(!running){running=true;if(pop.length===0){pop=Array(20).fill().map((_,i)=>{const g=randGenome(42+i);g.id='gen0_'+i;const r=evalGenome(g);return{genome:g,fitness:r.fitness,metrics:r.metrics,intensity:r.intensity};});gen=0;}loop();document.getElementById('btnStart').disabled=true;document.getElementById('btnPause').disabled=false;document.getElementById('btnStep').disabled=false;}};
document.getElementById('btnPause').onclick=()=>{running=false;cancelAnimationFrame(animId);document.getElementById('btnStart').disabled=false;document.getElementById('btnPause').disabled=true;};
document.getElementById('btnStep').onclick=()=>{if(!running){step();}};
document.getElementById('btnReset').onclick=()=>{running=false;cancelAnimationFrame(animId);pop=[];gen=0;ctx.clearRect(0,0,256,256);cctx.clearRect(0,0,chart.width,chart.height);popGrid.innerHTML='';document.getElementById('statGen').textContent=0;document.getElementById('statBestFit').textContent=0;document.getElementById('statAvgFit').textContent=0;};
</script>
</body>
</html>'''

with open('motor/evolution-viewer.html', 'w') as f:
    f.write(html)
print('Done')
