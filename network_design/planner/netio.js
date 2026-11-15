function loadNet(obj, key){
  S.nodes=new Map(); obj.nodes.forEach((n,k)=>S.nodes.set(String(n.id),{id:String(n.id), mw:+n.mw||0, kv:+n.kv||0, x:n.x??null, y:n.y??null}));
  S.edges=obj.edges.filter(e=>S.nodes.has(String(e.a))&&S.nodes.has(String(e.b))&&e.a!==e.b).map(e=>({a:String(e.a), b:String(e.b), km:+e.km||1}));
  S.cc=(obj.cc||[]).map(String).filter(c=>S.nodes.has(c)).slice(0,2); S.design=null; S.tapped=null; S.presetKey=key||null; S.edited=false;
  if([...S.nodes.values()].some(n=>n.x===null||n.y===null)) layout(); else fit();
  if(!S.cc.length) S.cc=autoCC(); draw(); showResults(); }
function fit(){ const xs=[...S.nodes.values()].map(n=>n.x), ys=[...S.nodes.values()].map(n=>n.y); if(!xs.length) return;
  const x0=Math.min(...xs), x1=Math.max(...xs), y0=Math.min(...ys), y1=Math.max(...ys); if(S.bg) return;
  const sx=920/((x1-x0)||1), sy=620/((y1-y0)||1), s=Math.min(sx,sy); for(const n of S.nodes.values()){ n.x=40+(n.x-x0)*s; n.y=40+(n.y-y0)*s; } }
function layout(){ const N=[...S.nodes.values()]; N.forEach((n,i)=>{ if(n.x===null){ n.x=500+300*Math.cos(2*Math.PI*i/N.length); n.y=350+250*Math.sin(2*Math.PI*i/N.length);} });
  for(let it=0;it<400;it++){ const F=new Map(N.map(n=>[n.id,[0,0]]));
    for(let i=0;i<N.length;i++) for(let j=i+1;j<N.length;j++){ const a=N[i],b=N[j]; let dx=a.x-b.x, dy=a.y-b.y; const d2=dx*dx+dy*dy+0.01, f=3000/d2; F.get(a.id)[0]+=dx*f; F.get(a.id)[1]+=dy*f; F.get(b.id)[0]-=dx*f; F.get(b.id)[1]-=dy*f; }
    for(const e of S.edges){ const a=S.nodes.get(e.a), b=S.nodes.get(e.b); const dx=b.x-a.x, dy=b.y-a.y; const d=Math.sqrt(dx*dx+dy*dy)+0.01, f=(d-60)*0.02; F.get(a.id)[0]+=dx/d*f*d; F.get(a.id)[1]+=dy/d*f*d; F.get(b.id)[0]-=dx/d*f*d; F.get(b.id)[1]-=dy/d*f*d; }
    const step=Math.max(0.02, 1-it/400); for(const n of N){ const [fx,fy]=F.get(n.id); const m=Math.sqrt(fx*fx+fy*fy)||1; n.x+=fx/m*Math.min(m,10)*step; n.y+=fy/m*Math.min(m,10)*step; } }
  fit(); }

