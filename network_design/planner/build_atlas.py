# Offline basemap for the Southeast (TN/AL/GA/MS/AR): water (rivers + lakes), county and state lines, town labels.
import json, re
from shapely.geometry import shape, box, Polygon, MultiPolygon, LineString, MultiLineString, mapping
from shapely.ops import unary_union, linemerge
BB=(-91.6,33.0,-82.6,37.3); B=box(*BB)
def topo(fn, obj):
    t=json.load(open(fn)); sc,tr=t['transform']['scale'],t['transform']['translate']; arcs=[]
    for a in t['arcs']:
        x=y=0; pts=[]
        for dx,dy in a: x+=dx; y+=dy; pts.append((x*sc[0]+tr[0], y*sc[1]+tr[1]))
        arcs.append(pts)
    def ring(ix):
        out=[]
        for i in ix:
            p=arcs[i] if i>=0 else arcs[~i][::-1]
            out.extend(p if not out else p[1:])
        return out
    feats=[]
    for g in t['objects'][obj]['geometries']:
        ps=[g['arcs']] if g['type']=='Polygon' else g['arcs'] if g['type']=='MultiPolygon' else []
        ok=lambda r: len(r)>=4
        pl=[Polygon(ring(p[0]),[x for x in (ring(r) for r in p[1:]) if ok(x)]) for p in ps if ok(ring(p[0]))]
        if not pl: continue
        geo=MultiPolygon(pl).buffer(0)
        feats.append((g.get('id'), g.get('properties',{}).get('name'), geo))
    return feats
def lines(geom, tol):
    g=geom.simplify(tol, preserve_topology=True)
    parts=[]; G=getattr(g,'geoms',[g])
    for p in G:
        if p.is_empty: continue
        if p.geom_type=='Polygon': parts += [p.exterior]+list(p.interiors)
        elif p.geom_type=='MultiPolygon': parts += [r for q in p.geoms for r in [q.exterior]+list(q.interiors)]
        elif 'LineString' in p.geom_type: parts += list(getattr(p,'geoms',[p]))
    return [[[round(x,3),round(y,3)] for x,y in r.coords] for r in parts if len(r.coords)>=2]
def polys(geom, tol, minarea):
    g=geom.simplify(tol, preserve_topology=True); out=[]
    for p in getattr(g,'geoms',[g]):
        if p.geom_type!='Polygon' or p.area<minarea: continue
        out.append([[[round(x,3),round(y,3)] for x,y in r.coords] for r in [p.exterior]+list(p.interiors)])
    return out
P='us-atlas-3.0.1/package/'
counties=[g.intersection(B) for _,_,g in topo(P+'counties-10m.json','counties') if g.intersects(B)]
states=[(n,g) for _,n,g in topo(P+'states-10m.json','states') if g.intersects(B)]
cl=linemerge(unary_union([c.boundary for c in counties]).intersection(B))
sl=linemerge(unary_union([g.boundary for _,g in states]).intersection(B))
water=unary_union([shape(json.load(open('rivers_clip.json'))).buffer(0), shape(json.load(open('lakes_clip.json'))).buffer(0)])
water=water.buffer(0.004,quad_segs=3).buffer(-0.0028,quad_segs=3)
W=polys(water, 0.0012, 2.5e-5)
A=dict(bbox=BB, county=lines(cl,0.004), state=lines(sl,0.003), water=W,
       states=[[n, round(g.intersection(B).representative_point().y,2), round(g.intersection(B).representative_point().x,2)] for n,g in states])
# town labels: the preset towns (big cities first)
T=json.load(open('/home/claude/geo/towns.json'))
A['towns']=T
s=json.dumps(A,separators=(',',':')); open('atlas.json','w').write(s)
print(len(s), {k:len(v) for k,v in A.items() if isinstance(v,list)})
# compact: each ring = "lon0,lat0,dx,dy,..." in 1/1000 degree, rings joined by ";" polygons by "|"
def enc(r):
    q=[(round(x*1000),round(y*1000)) for x,y in r]; out=[q[0][0],q[0][1]]
    for (a,b),(c,d) in zip(q,q[1:]): out += [c-a,d-b]
    return ",".join(map(str,out))
C=dict(bbox=BB, county=";".join(enc(r) for r in A['county']), state=";".join(enc(r) for r in A['state']),
       water="|".join(";".join(enc(r) for r in p) for p in A['water']), states=A['states'], towns=A['towns'])
s=json.dumps(C,separators=(',',':')); open('atlas_c.json','w').write(s); print("compact",len(s))
