import json, re
exec(open('assemble.py').read().split("s=open('template.html')")[0])   # loads pre and EV
s=open('template2.html').read()
s=s.replace('/*PRESETS*/[]',json.dumps(pre,separators=(',',':'))).replace('/*EVIDENCE*/[]',json.dumps(EV)).replace('/*ATLAS*/null',open('atlas.json').read())
s=s.replace('/*MODEL*/',open('model.js').read()).replace('/*NETIO*/',open('netio.js').read())
open('qkd_grid_optimizer.html','w').write(s); print(len(s))
