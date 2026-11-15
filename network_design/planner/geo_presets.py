# Put every city preset on the real map: each substation goes to its town's coordinates,
# towns with several substations keep their relative layout, scaled so in-town lines match their km.
import json, re, math, statistics
T = {
 "knoxville_r1": {"KNOXVILLE":(35.961,-83.921),"CLINTON":(36.103,-84.132),"OAK RIDGE":(36.010,-84.270),"POWELL":(36.031,-84.030),"SEYMOUR":(35.886,-83.773),
   "SEVIERVILLE":(35.868,-83.562),"NEW MARKET":(36.105,-83.553),"DANDRIDGE":(36.015,-83.415),"LOUISVILLE":(35.822,-84.048),"MARYVILLE":(35.757,-83.970),
   "STRAWBERRY PLAINS":(36.045,-83.685),"CORRYTON":(36.142,-83.785),"KODAK":(35.973,-83.620),"RUTLEDGE":(36.276,-83.515),"KINGSTON":(35.881,-84.508),"LENOIR CITY":(35.797,-84.256)},
 "nashville_r1": {"ASHLAND CITY":(36.274,-87.064),"NASHVILLE":(36.163,-86.781),"JOELTON":(36.318,-86.869),"ANTIOCH":(36.060,-86.672),"FRANKLIN":(35.925,-86.869),
   "SMYRNA":(35.983,-86.519),"BRENTWOOD":(36.033,-86.783),"HERMITAGE":(36.196,-86.622),"DICKSON":(36.077,-87.388),"GOODLETTSVILLE":(36.323,-86.713),
   "LA VERGNE":(36.016,-86.582),"MADISON":(36.256,-86.715),"MOUNT JULIET":(36.200,-86.519),"HENDERSONVILLE":(36.305,-86.620),"MURRAY":(36.610,-88.315),"GALLATIN":(36.388,-86.447)},
 "huntsville_r1": {"ARAB":(34.328,-86.496),"HUNTSVILLE":(34.730,-86.586),"ATHENS":(34.803,-86.972),"HARVEST":(34.856,-86.751),"TONEY":(34.897,-86.725),
   "MADISON":(34.699,-86.748),"HAZEL GREEN":(34.932,-86.572),"NEW MARKET":(34.910,-86.428),"OWENS CROSS ROADS":(34.588,-86.459),"NEW HOPE":(34.537,-86.394),
   "HARTSELLE":(34.443,-86.935),"TUSCUMBIA":(34.731,-87.702),"DECATUR":(34.606,-86.983),"WINCHESTER":(35.186,-86.112)},
 "memphis_r1": {"HORN LAKE":(34.955,-90.035),"SOUTHAVEN":(34.989,-90.013),"MEMPHIS":(35.149,-90.049),"OLIVE BRANCH":(34.962,-89.830),"WEST MEMPHIS":(35.147,-90.185),
   "WALLS":(34.958,-90.153),"MARION":(35.215,-90.196),"ARLINGTON":(35.296,-89.661),"BRIGHTON":(35.484,-89.725),"COLLIERVILLE":(35.042,-89.664),"MOSCOW":(35.062,-89.403),
   "CORDOVA":(35.156,-89.776),"GERMANTOWN":(35.087,-89.810),"EARLE":(35.275,-90.467),"FORREST CITY":(35.008,-90.790),"HUGHES":(34.949,-90.471),"MILLINGTON":(35.341,-89.897)},
 "atlanta_r1": {"ATLANTA":(33.749,-84.388),"FAYETTEVILLE":(33.449,-84.455),"FAIRBURN":(33.567,-84.581),"UNION CITY":(33.587,-84.542),"DOUGLASVILLE":(33.751,-84.747),
   "FOREST PARK":(33.622,-84.369),"CONLEY":(33.645,-84.326),"ELLENWOOD":(33.627,-84.273),"STOCKBRIDGE":(33.544,-84.234),"AUSTELL":(33.813,-84.634),"MABLETON":(33.819,-84.582),
   "SMYRNA":(33.884,-84.514),"MARIETTA":(33.953,-84.550),"ROSWELL":(34.023,-84.362),"TUCKER":(33.855,-84.217),"NORCROSS":(33.941,-84.214),"DECATUR":(33.775,-84.296),"STONE MOUNTAIN":(33.808,-84.170)}}
town = lambda s: re.sub(r" \d+$", "", s)
P = json.load(open("presets.json"))
for q in P:
    if q["key"] not in T: continue
    tc = T[q["key"]]; N = {n["id"]: n for n in q["nodes"]}
    grp = {}
    for n in q["nodes"]: grp.setdefault(town(n["id"]), []).append(n)
    cen = {t: (sum(n["x"] for n in v)/len(v), sum(n["y"] for n in v)/len(v)) for t, v in grp.items()}
    r = [e["km"] / max(1e-6, math.dist((N[e["a"]]["x"], N[e["a"]]["y"]), (N[e["b"]]["x"], N[e["b"]]["y"])))
         for e in q["edges"] if town(e["a"]) == town(e["b"])]
    s = statistics.median(r)   # km per layout unit
    for n in q["nodes"]:
        t = town(n["id"]); la, lo = tc[t]; cx, cy = cen[t]
        dx, dy = (n["x"] - cx) * s, (n["y"] - cy) * s       # km east, km south
        n["lat"] = round(la - dy / 111.0, 5); n["lon"] = round(lo + dx / (111.0 * math.cos(math.radians(la))), 5)
    rr = [math.dist(((N[e["a"]]["lon"]-N[e["b"]]["lon"])*111*math.cos(math.radians(N[e["a"]]["lat"])),0),((N[e["a"]]["lat"]-N[e["b"]]["lat"])*111,0)) for e in q["edges"]]
    geo = [111*math.hypot(N[e["a"]]["lat"]-N[e["b"]]["lat"], (N[e["a"]]["lon"]-N[e["b"]]["lon"])*math.cos(math.radians(N[e["a"]]["lat"])))/e["km"] for e in q["edges"]]
    print(q["key"], "scale km/unit", round(s, 3), "median map/line km", round(statistics.median(geo), 2))
json.dump(P, open("presets.json", "w"))
