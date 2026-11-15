import json, re
from shapely.geometry import shape, box
from shapely.ops import unary_union, linemerge
exec(open('build_atlas.py').read().split("P='us-atlas")[0])   # topo(), lines(), polys(), BB, B
P='us-atlas-3.0.1/package/'
counties=[g.intersection(B) for _,_,g in topo(P+'counties-10m.json','counties') if g.intersects(B)]
states=[(n,g) for _,n,g in topo(P+'states-10m.json','states') if g.intersects(B)]
cl=linemerge(unary_union([c.boundary for c in counties]).intersection(B))
sl=linemerge(unary_union([g.boundary for _,g in states]).intersection(B))
def feats(f, keep=lambda p:True):
    return [(x['properties'], shape(x['geometry']).intersection(B)) for x in json.load(open(f+'.geojson'))['features'] if x['geometry'] and keep(x['properties']) and shape(x['geometry']).intersects(B)]
lakes=unary_union([g.buffer(0) for _,g in feats('ne_10m_lakes')+feats('ne_10m_lakes_north_america')])
riv=[(p.get('scalerank',9), g) for p,g in feats('ne_10m_rivers_lake_centerlines')+feats('ne_10m_rivers_north_america')]
big=linemerge(unary_union([g for r,g in riv if r<=7])); small=linemerge(unary_union([g for r,g in riv if r>7]))
roads=feats('ne_10m_roads'); maj=linemerge(unary_union([g for p,g in roads if p['type'] in('Major Highway','Beltway')])); sec=linemerge(unary_union([g for p,g in roads if p['type'] not in('Major Highway','Beltway')]))
urban=unary_union([g.buffer(0) for _,g in feats('ne_10m_urban_areas')])
def enc(r):
    q=[(round(x*1000),round(y*1000)) for x,y in r]; out=[q[0][0],q[0][1]]
    for (a,b),(c,d) in zip(q,q[1:]): out += [c-a,d-b]
    return ",".join(map(str,out))
L=lambda g,t: ";".join(enc(r) for r in lines(g,t))
PP=lambda g,t,m: "|".join(";".join(enc(r) for r in p) for p in polys(g,t,m))
st=[[n, round(g.intersection(B).representative_point().y,2), round(g.intersection(B).representative_point().x,2)] for n,g in states]
C=dict(bbox=BB, county=L(cl,.003), state=L(sl,.002), lake=PP(lakes,.001,1e-6), urban=PP(urban,.002,1e-5), river=L(big,.0015), stream=L(small,.002),
       hwy=L(maj,.0015), road=L(sec,.002), states=st, towns=json.load(open('towns.json')))
s=json.dumps(C,separators=(',',':')); open('atlas_c.json','w').write(s); print(len(s), {k:len(v) for k,v in C.items() if isinstance(v,str)})
