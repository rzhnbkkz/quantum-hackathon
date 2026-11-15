// ---------------------------------------------------------------- graph helpers
function adj(){ const A=new Map(); for(const n of S.nodes.keys()) A.set(n,[]); S.edges.forEach((e,i)=>{ if(A.has(e.a)&&A.has(e.b)){A.get(e.a).push([e.b,e.km,i]);A.get(e.b).push([e.a,e.km,i]);} }); return A; }
function dijkstra(A, src){ const d=new Map([[src,0]]), prev=new Map(), done=new Set(); const Q=[[0,src]];
  while(Q.length){ Q.sort((x,y)=>x[0]-y[0]); const [du,u]=Q.shift(); if(done.has(u)) continue; done.add(u);
    for(const [v,w,i] of A.get(u)){ const nd=du+w; if(!d.has(v)||nd<d.get(v)-1e-12){ d.set(v,nd); prev.set(v,[u,i]); Q.push([nd,v]); } } }
  return {d,prev}; }
function pathEdges(prev, s){ const E=[]; let u=s; while(prev.has(u)){ const [p,i]=prev.get(u); E.push(i); u=p; } return E; }
function autoCC(){ const A=adj(); const ids=[...S.nodes.keys()]; if(!ids.length) return [];
  let best=null; for(const s of ids){ const {d}=dijkstra(A,s); if(d.size<ids.length*0.6) continue; let sum=0; for(const v of d.values()) sum+=v;
    const sc=(S.nodes.get(s).kv||0)*1e6 - sum; if(!best||sc>best[0]) best=[sc,s]; }
  const c1=best?best[1]:ids[0]; const H=P().H;
  // backup: closest-to-center node within H hops (BFS) other than c1
  const hop=new Map([[c1,0]]), q=[c1]; while(q.length){const u=q.shift(); for(const [v] of A.get(u)) if(!hop.has(v)){hop.set(v,hop.get(u)+1); if(hop.get(v)<=H) q.push(v);} }
  let b2=null; for(const [s,h] of hop){ if(s===c1||h>H) continue; const {d}=dijkstra(A,s); let sum=0; for(const v of d.values()) sum+=v; if(!b2||sum<b2[0]) b2=[sum,s]; }
  return b2? [c1,b2[1]] : [c1]; }

// ---------------------------------------------------------------- model (mirrors network_design/v11.py)
function buildModel(p){
  const A=adj(); const cc=S.cc.filter(c=>S.nodes.has(c)); if(cc.length===0) return null;
  const feasible=new Set(); S.edges.forEach((e,i)=>{ if(e.km*p.db<=p.loss+1e-9) feasible.add(i); });
  const dist=new Map(); for(const c of cc){ const {d}=dijkstra(A,c); for(const [s,v] of d) dist.set(s, Math.min(dist.get(s)??Infinity, v)); }
  const value=new Map(); for(const [s,n] of S.nodes) if(!cc.includes(s) && dist.has(s)) value.set(s, n.mw*dist.get(s));
  // feasible adjacency
  const F=new Map(); for(const n of S.nodes.keys()) F.set(n,[]); for(const i of feasible){ const e=S.edges[i]; F.get(e.a).push([e.b,i]); F.get(e.b).push([e.a,i]); }
  const paths=new Map(); const cc2=cc[1];
  const targets=[...value.keys()]; if(cc2) targets.push(cc2);
  // DFS from each control center up to H hops
  const reach=new Map(); // target -> list of {E:[edge idx], R:[relays]}
  for(const c of cc){ const stack=[[c,[c],[]]]; let count=0;
    while(stack.length && count<200000){ const [u,nodes,E]=stack.pop(); count++;
      if(E.length>0){ const t=u; if((!cc.includes(t) && value.has(t)) || (t===cc2 && c===cc[0])){ if(!reach.has(t)) reach.set(t,[]); const L=reach.get(t); if(L.length<80) L.push({E:E.slice(), R:nodes.slice(1,-1).filter(n=>!cc.includes(n))}); } }
      if(E.length>=p.H) continue;
      for(const [v,i] of F.get(u)){ if(nodes.includes(v)) continue; stack.push([v,[...nodes,v],[...E,i]]); } } }
  for(const t of targets) if(reach.has(t)) paths.set(t, reach.get(t));
  const ccReach = !!(cc2 && paths.has(cc2));
  let maxValue=0; for(const [s,v] of value) if(paths.has(s)) maxValue+=v;
  // traffic per feasible edge (PQC baseline: shortest route from nearest control center)
  const traffic=new Float64Array(S.edges.length); const routes0=baseRoutes(A,cc);
  for(const [s,E] of routes0) if(!cc.includes(s)) for(const i of E) traffic[i]+=S.nodes.get(s).mw;   // objective: substations only (as in v11.traffic)
  const through0=new Float64Array(S.edges.length); for(const [s,E] of routes0) for(const i of E) through0[i]+=S.nodes.get(s).mw;   // attacks: incl. backup control center
  let tot=0; for(const i of feasible) tot+=traffic[i]*S.edges[i].km; const scale= tot>0 ? maxValue/tot : 0;
  return {A,cc,feasible,value,paths,ccReach,maxValue,traffic,through0,scale,routes0,p};
}
function baseRoutes(A,cc){ const R=new Map(); const runs=cc.map(c=>dijkstra(A,c));
  for(const s of S.nodes.keys()){ if(cc.includes(s) && s!==cc[1]) continue; let best=null;
    runs.forEach((r,k)=>{ if(cc[k]===s) return; if(r.d.has(s) && (!best || r.d.get(s)<best[0])) best=[r.d.get(s), pathEdges(r.prev,s)]; });
    if(best) R.set(s,best[1]); }
  return R; }
function evaluate(M, Y, T){ // Y: Set of edge idx
  const used=new Set(), prot=[], chosen=new Map(); let val=0;
  const order=(M.ccReach?[M.cc[1]]:[]).concat([...M.paths.keys()].filter(s=>s!==M.cc[1]).sort((a,b)=>M.value.get(b)-M.value.get(a)));
  for(const s of order){ let best=null;
    for(const pth of M.paths.get(s)){ if(!pth.E.every(i=>Y.has(i))) continue; const nw=pth.R.filter(n=>!used.has(n));
      if(used.size+nw.length<=T && (!best || nw.length<best.nw.length)) best={nw,pth}; }
    if(best){ best.nw.forEach(n=>used.add(n)); prot.push(s); chosen.set(s,best.pth); val+=M.value.get(s)||0; } }
  const ccOK = !M.ccReach || prot.includes(M.cc[1]);
  return {val: ccOK? val : -1, used, prot, chosen, ccOK}; }
function objective(M,Y,T){ const ev=evaluate(M,Y,T); if(ev.val<0) return {...ev, obj:-1e18+ev.val};
  let det=0; for(const i of Y) det+=M.traffic[i]*S.edges[i].km;
  let val=ev.val;
  if(M.p.n1 && Y.size){ // survive one QKD link failure: score half on the normal design, half on its worst single-link failure
    let worst=Infinity; for(const f of Y){ const Y2=new Set(Y); Y2.delete(f); const e2=evaluate(M,Y2,T); worst=Math.min(worst, e2.prot.reduce((s,x)=>s+(M.value.get(x)||0),0)); } val=0.5*ev.val+0.5*worst; }
  return {...ev, obj: val + M.p.mu*M.scale*det}; }
// what is still quantum-safe if each QKD link fails in turn
function n1Check(M,Y){ const T=M.p.T, mw=ev=>ev.prot.reduce((s,x)=>s+S.nodes.get(x).mw,0); const base=mw(evaluate(M,Y,T)); let worst=Infinity, wf=-1;
  for(const f of Y){ const Y2=new Set(Y); Y2.delete(f); const v=mw(evaluate(M,Y2,T)); if(v<worst){ worst=v; wf=f; } }
  if(!Y.size) worst=base; return {base, worst, wf, kept: base>0? worst/base : 1}; }

function solve(M){
  const {K,T}=M.p; const feas=[...M.feasible]; const t0=performance.now();
  const greedy=(start)=>{ let Y=new Set(start); let cur=objective(M,Y,T).obj;
    for(let it=0; it<200 && Y.size<K; it++){ let best=null;
      const cands=[]; for(const [s,L] of M.paths) for(const pth of L){ const nw=pth.E.filter(i=>!Y.has(i)); if(nw.length && Y.size+nw.length<=K) cands.push(nw); }
      for(const i of feas) if(!Y.has(i)) cands.push([i]);
      for(const nw of cands){ const Y2=new Set([...Y,...nw]); const o=objective(M,Y2,T).obj; const g=(o-cur)/nw.length; if(o>cur+1e-9 && (!best||g>best[0])) best=[g,Y2,o]; }
      if(!best) break; Y=best[1]; cur=best[2]; }
    return Y; };
  const local=(Y)=>{ let cur=objective(M,Y,T).obj; let improved=true, rounds=0;
    while(improved && rounds<20){ improved=false; rounds++;
      for(const out of [...Y]){ for(const inn of feas){ if(Y.has(inn)) continue; const Y2=new Set(Y); Y2.delete(out); Y2.add(inn); const o=objective(M,Y2,T).obj; if(o>cur+1e-9){ Y=Y2; cur=o; improved=true; break; } } if(improved) break; }
      if(!improved && Y.size<K){ for(const inn of feas){ if(Y.has(inn)) continue; const Y2=new Set([...Y,inn]); const o=objective(M,Y2,T).obj; if(o>cur+1e-9){ Y=Y2; cur=o; improved=true; break; } } } }
    return Y; };
  // start: cheapest control-center chain that fits
  let start=[]; if(M.ccReach){ const L=[...M.paths.get(M.cc[1])].filter(p=>p.E.length<=K && p.R.length<=T).sort((a,b)=>a.E.length-b.E.length || a.R.length-b.R.length); if(L.length) start=L[0].E; }
  // several starting points: control-center chain, busiest fiber first, empty
  const busy=[...feas].sort((a,b)=>M.traffic[b]*S.edges[b].km-M.traffic[a]*S.edges[a].km).slice(0,Math.max(1,Math.floor(K/2)));
  let best=null, bestO=-Infinity; const consider=Y=>{ const o=objective(M,Y,T).obj; if(o>bestO+1e-9){ best=Y; bestO=o; } };
  for(const st of [start, [...new Set([...start,...busy])].slice(0,K), []]) consider(local(greedy(st)));
  let seed=7; const rnd=()=>{ seed=(seed*16807)%2147483647; return seed/2147483647; };
  const budgetMs = 400;
  for(let r=0; r<60 && performance.now()-t0<budgetMs; r++){ const Y=[...best]; const drop=1+Math.floor(rnd()*Math.min(4,Y.length||1));
    for(let k=0;k<drop && Y.length;k++) Y.splice(Math.floor(rnd()*Y.length),1);
    if(rnd()<0.5){ const add=feas[Math.floor(rnd()*feas.length)]; if(!Y.includes(add) && Y.length<K) Y.push(add); }
    consider(local(greedy(Y))); }
  if(M.p.n1) best=n1Repair(M,best,t0);
  return {Y:best, ms:performance.now()-t0}; }
// N-1 mode: multi-link moves that add a detour path (its missing links) and drop the same number of least useful links
function n1Repair(M,Y,t0){ const {T}=M.p; let cur=objective(M,Y,T).obj; let improved=true;
  while(improved && performance.now()-t0<2500){ improved=false;
    const marg=[...Y].map(i=>{ const Y2=new Set(Y); Y2.delete(i); return [cur-objective(M,Y2,T).obj,i]; }).sort((a,b)=>a[0]-b[0]);
    const seen=new Set();
    for(const [s,L] of M.paths){ for(const pth of L){ const nw=pth.E.filter(i=>!Y.has(i)); if(!nw.length || nw.length>2 || nw.length===pth.E.length) continue;
        const key=nw.slice().sort().join(","); if(seen.has(key)) continue; seen.add(key);
        const room=M.p.K-Y.size, drop=Math.max(0,nw.length-room); const Y2=new Set(Y); let k=0;
        for(const [,i] of marg){ if(k>=drop) break; if(pth.E.includes(i)) continue; Y2.delete(i); k++; }
        nw.forEach(i=>Y2.add(i)); if(Y2.size>M.p.K) continue; const o=objective(M,Y2,T).obj;
        if(o>cur+1e-9){ Y=Y2; cur=o; improved=true; break; } }
      if(improved) break; } }
  return Y; }

// ---------------------------------------------------------------- attacks and resilience
function analyze(M, Y){
  const T=M.p.T; const ev=evaluate(M,Y,T);
  // routes: QKD path if protected, else shortest route
  const R=new Map(); for(const [s,E] of M.routes0) R.set(s,{E, q:false, R:[]});
  for(const [s,pth] of ev.chosen) R.set(s,{E:pth.E, q:true, R:pth.R});
  const through=new Float64Array(S.edges.length); for(const [s,r] of R) for(const i of r.E) through[i]+=S.nodes.get(s).mw;
  let worstPQC=0, worstPQCe=-1; const thr0=M.through0; for(let i=0;i<S.edges.length;i++) if(thr0[i]>worstPQC){worstPQC=thr0[i]; worstPQCe=i;}
  let worst=0, worstE=-1; for(let i=0;i<S.edges.length;i++){ if(Y.has(i)) continue; if(through[i]>worst){worst=through[i]; worstE=i;} }
  let kmAll=0, kmQ=0; S.edges.forEach((e,i)=>{ kmAll+=e.km; if(Y.has(i)) kmQ+=e.km; });
  let mwProt=0; for(const s of ev.prot) mwProt+=S.nodes.get(s).mw;
  let mwAll=0; for(const n of S.nodes.values()) mwAll+=n.mw;
  let worstTN=0, worstTNn=null; for(const n of ev.used){ let m=0; for(const [s,r] of R) if(r.q && r.R.includes(n)) m+=S.nodes.get(s).mw; if(m>worstTN){worstTN=m; worstTNn=n;} }
  const cut=cutAnalysis(M.cc);
  return {ev, R, through, worst, worstE, worstPQC, worstPQCe, tapShare: kmAll? kmQ/kmAll : 0, mwProt, mwAll, worstTN, worstTNn, cut}; }
function bridges(nodes, E){ // Tarjan on multigraph by edge index
  const A=new Map(); nodes.forEach(n=>A.set(n,[])); E.forEach((e,i)=>{ A.get(e[0]).push([e[1],i]); A.get(e[1]).push([e[0],i]); });
  const tin=new Map(), low=new Map(); let t=0; const out=[];
  for(const r of nodes){ if(tin.has(r)) continue; const st=[[r,-1,0]]; tin.set(r,t); low.set(r,t); t++;
    while(st.length){ const top=st[st.length-1]; const [u,pe]=top; const L=A.get(u);
      if(top[2]<L.length){ const [v,i]=L[top[2]++]; if(i===pe) continue;
        if(tin.has(v)) low.set(u,Math.min(low.get(u),tin.get(v))); else { tin.set(v,t); low.set(v,t); t++; st.push([v,i,0]); } }
      else { st.pop(); if(st.length){ const p=st[st.length-1][0]; low.set(p,Math.min(low.get(p),low.get(u))); if(low.get(u)>tin.get(p)) out.push(pe); } } } }
  return out; }
function cutAnalysis(cc){
  const ROOT = cc.length>1 ? "_CC_" : cc[0];
  const nodes=[...S.nodes.keys()].concat(cc.length>1?["_CC_"]:[]); const E=S.edges.filter(e=>S.nodes.has(e.a)&&S.nodes.has(e.b)).map(e=>[e.a,e.b,e.km]); if(cc.length>1) cc.forEach(c=>E.push([c,"_CC_",0]));
  const worstCut=(E)=>{ const br=bridges(nodes,E); let w=0; for(const bi of br){ const keep=E.filter((_,i)=>i!==bi); const A=new Map(); nodes.forEach(n=>A.set(n,[])); keep.forEach(e=>{A.get(e[0]).push(e[1]);A.get(e[1]).push(e[0]);});
      const seen=new Set([ROOT]), q=[ROOT]; while(q.length){const u=q.shift(); for(const v of A.get(u)) if(!seen.has(v)){seen.add(v); q.push(v);} }
      let m=0; for(const [s,n] of S.nodes) if(!seen.has(s)) m+=n.mw; w=Math.max(w,m); } return {br:br.length, w}; };
  const before=worstCut(E); const added=[]; const A0=adj();
  for(let it=0; it<60; it++){ const br=new Set(bridges(nodes,E)); if(!br.size) break;
    // 2-edge-connected components
    const A=new Map(); nodes.forEach(n=>A.set(n,[])); E.forEach((e,i)=>{ if(!br.has(i)){A.get(e[0]).push(e[1]);A.get(e[1]).push(e[0]);} });
    const comp=new Map(); let c=0; for(const n of nodes){ if(comp.has(n)) continue; const q=[n]; comp.set(n,c); while(q.length){const u=q.shift(); for(const v of A.get(u)) if(!comp.has(v)){comp.set(v,c); q.push(v);} } c++; }
    const deg=new Array(c).fill(0); const TA=Array.from({length:c},()=>[]); for(const i of br){ const a=comp.get(E[i][0]), b=comp.get(E[i][1]); deg[a]++; deg[b]++; TA[a].push(b); TA[b].push(a); }
    const leaves=[]; for(let k=0;k<c;k++) if(deg[k]===1) leaves.push(k); if(leaves.length===0) break;
    if(leaves.length===1){ const root=comp.get(ROOT); if(root===leaves[0]) break; leaves.push(root); }
    const bfs=(s)=>{ const d=new Map([[s,0]]), q=[s]; while(q.length){const u=q.shift(); for(const v of TA[u]) if(!d.has(v)){d.set(v,d.get(u)+1); q.push(v);} } return d; };
    let pair=null; for(const a of leaves){ const d=bfs(a); for(const b of leaves){ if(b<=a) continue; const dd=d.get(b)??-1; if(!pair||dd>pair[0]) pair=[dd,a,b]; } }
    const mem=k=>nodes.filter(n=>comp.get(n)===k && n!=="_CC_");
    let choice=null; const ma=mem(pair[1]), mb=mem(pair[2]);
    for(const u of ma){ const {d}=dijkstra(A0,u); for(const v of mb){ if(u===v) continue; if(E.some(e=>(e[0]===u&&e[1]===v)||(e[0]===v&&e[1]===u))) continue; const km=d.get(v); if(km!==undefined && (!choice||km<choice[2])) choice=[u,v,km]; } }
    if(!choice) break; E.push(choice); added.push(choice); }
  const after=worstCut(E);
  return {bridgesBefore:before.br, worstBefore:before.w, worstAfter:after.w, added}; }

