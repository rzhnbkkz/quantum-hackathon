# qkd_grid_optimizer.html -> qkd_grid_optimizer_1280x720.html (fixed 1280x720 frame, 1920x1080 stage scaled 2/3)
s=open('qkd_grid_optimizer.html').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a; s=s.replace(a,b)
rep('</style>','''
html,body{width:1280px!important;height:720px!important;margin:0!important;overflow:hidden!important;background:var(--bg)}
#frame{position:relative;width:1280px;height:720px;overflow:hidden}
body.fit #stage{position:absolute!important;left:0!important;top:0!important;transform:scale(0.6666667)!important;transform-origin:0 0}
.fitbtn{display:none!important}
</style>''')
rep('<div id="stage">','<div id="frame"><div id="stage">')
rep('</div><!-- /stage -->','</div><!-- /stage --></div><!-- /frame -->')
rep('setFit(qs.has("fit")||qs.has("faces")||qs.has("slide")||(embedded && !qs.has("page")));','setFit(true);')
rep('window.addEventListener("resize",fitStage);','')
open('qkd_grid_optimizer_1280x720.html','w').write(s); print(len(s))
