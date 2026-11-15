import re, sys, json
def parse(path):
    txt=open(path).read()
    def mat(name):
        m=re.search(r"mpc\."+name+r"\s*=\s*\[(.*?)\];",txt,re.S)
        rows=[]
        for line in m.group(1).split('\n'):
            line=line.split('%')[0].strip().rstrip(';')
            if line: rows.append([float(v) for v in line.split()])
        return rows
    names=re.search(r"mpc\.bus_name\s*=\s*\{(.*?)\};",txt,re.S).group(1)
    names=[n for n in re.findall(r"'([^']*)'",names)]
    return mat('bus'),mat('branch'),names,float(re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)",txt).group(1))
