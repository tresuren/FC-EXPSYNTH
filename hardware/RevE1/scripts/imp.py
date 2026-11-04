import pcbnew,re,sys
from pcbnew import FromMM as MM, VECTOR2I
ses=open('route.ses').read()
def parse(s):
    toks=re.findall(r'\(|\)|"[^"]*"|[^\s()]+',s); pos=0
    def rd():
        nonlocal pos
        assert toks[pos]=='('; pos+=1; lst=[]
        while toks[pos]!=')':
            if toks[pos]=='(': lst.append(rd())
            else: lst.append(toks[pos].strip('"')); pos+=1
        pos+=1; return lst
    return rd()
t=parse(ses)
def find(l,name): return [x for x in l if isinstance(x,list) and x and x[0]==name]
net_out=find(find(t,'routes')[0] if find(t,'routes') else t,'network_out')[0]
bd=pcbnew.LoadBoard('FC-EXPSYNTH.kicad_pcb')
layers={'F.Cu':pcbnew.F_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu,'B.Cu':pcbnew.B_Cu}
nets=bd.GetNetsByName()
U=1/10000.0
nw=nv=0
for n in find(net_out,'net'):
    name=n[1]
    ni=nets.find(name)
    if ni==nets.end(): ni=nets.find('/'+name.lstrip('/'))
    if ni==nets.end(): print('net?',name); continue
    ni=ni.value()[1]
    for w in find(n,'wire'):
        for p in find(w,'path'):
            lay=layers[p[1]]; wd=float(p[2])*U
            c=[float(v)*U for v in p[3:]]
            for i in range(0,len(c)-2,2):
                tr=pcbnew.PCB_TRACK(bd); tr.SetStart(VECTOR2I(MM(c[i]),MM(-c[i+1]))); tr.SetEnd(VECTOR2I(MM(c[i+2]),MM(-c[i+3])))
                tr.SetWidth(MM(wd)); tr.SetLayer(lay); tr.SetNet(ni); bd.Add(tr); nw+=1
    for v in find(n,'via'):
        m=re.search(r'_(\d+):(\d+)_um',v[1]); d,dr=int(m.group(1))/1000,int(m.group(2))/1000
        x,y=float(v[2])*U,float(v[3])*U
        via=pcbnew.PCB_VIA(bd); via.SetPosition(VECTOR2I(MM(x),MM(-y))); via.SetWidth(MM(d)); via.SetDrill(MM(dr))
        via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); via.SetNet(ni); bd.Add(via); nv+=1
print('segments',nw,'vias',nv)
for z in bd.Zones():
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetLocalClearance(MM(0.15)); z.SetMinThickness(MM(0.15))
pcbnew.ZONE_FILLER(bd).Fill(bd.Zones())
bd.BuildConnectivity()
print('unrouted', bd.GetConnectivity().GetUnconnectedCount(False))
pcbnew.SaveBoard('FC-EXPSYNTH_routed.kicad_pcb',bd)
