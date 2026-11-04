# -*- coding: utf-8 -*-
# B実験：外観画像＋図面シート(drawing_v14)からの住宅マッシング  Rhino / IronPython / RhinoCommon
# 単位mm。Z上、道路は-Y側、x=0は左の箱の左端、y=0は正面の外壁線（1階平面 py=850）。1m=50px。
import Rhino, scriptcontext as sc, System, math
import Rhino.Geometry as G
d=sc.doc; tol=d.ModelAbsoluteTolerance; M=1000.0
LOG=[]

def P(x,y,z=0): return G.Point3d(x*M,y*M,z*M)
def path(segs):
    pts=[]
    for s in segs:
        if s[0]=='L': pts.append(P(s[1],s[2]))
        else:
            cx,cy,r,a0,a1=s[1],s[2],s[3],s[4],s[5]
            n=max(2,int(abs(a1-a0)/5.0))
            for k in range(n+1):
                a=math.radians(a0+(a1-a0)*k/float(n))
                pts.append(P(cx+r*math.cos(a),cy+r*math.sin(a)))
    out=[]
    for p in pts:
        if not out or out[-1].DistanceTo(p)>1: out.append(p)
    if out[0].DistanceTo(out[-1])>1: out.append(G.Point3d(out[0]))
    else: out[-1]=G.Point3d(out[0])
    return G.PolylineCurve(out)
def ext(crv,z0,z1):
    c=crv.DuplicateCurve(); c.Translate(G.Vector3d(0,0,z0*M))
    s=G.Surface.CreateExtrusion(c,G.Vector3d(0,0,(z1-z0)*M))
    b=G.Brep.CreateFromSurface(s).CapPlanarHoles(tol)
    if b.SolidOrientation==G.BrepSolidOrientation.Inward: b.Flip()
    return b
def box(x0,y0,z0,x1,y1,z1):
    return G.Box(G.BoundingBox(x0*M,y0*M,z0*M,x1*M,y1*M,z1*M)).ToBrep()
def add(b,layer,name):
    a=Rhino.DocObjects.ObjectAttributes(); a.LayerIndex=d.Layers.FindByFullPath(layer,-1); a.Name=name
    return d.Objects.AddBrep(b,a)
def get(name):
    for o in d.Objects:
        if o.Attributes.Name==name: return o
    return None
def diff(b,cutters):
    for c in cutters:
        if c.SolidOrientation==G.BrepSolidOrientation.Inward: c.Flip()
    r=G.Brep.CreateBooleanDifference([b],cutters,tol)
    if r is None or len(r)==0:
        LOG.append('diff failed'); return b
    if len(r)>1: LOG.append('pieces %d'%len(r))
    return max(r,key=lambda x:x.GetVolume())
def union(bs):
    r=G.Brep.CreateBooleanUnion(bs,tol)
    if r is None or len(r)==0:
        LOG.append('union failed'); return bs
    return list(r)
def replace(name,b):
    o=get(name); d.Objects.Replace(o.Id,b)
def fin():
    for vw in d.Views:
        if vw.ActiveViewport.Name=='Perspective':
            vw.ActiveViewport.ZoomExtents()
    d.Views.Redraw()

# --- 0 初期化：全削除・レイヤー・Shaded ---
d.Objects.UnselectAll()
for i in [o.Id for o in d.Objects]: d.Objects.Delete(i,True)
d.AdjustModelUnitSystem(Rhino.UnitSystem.Millimeters,False)
cols={'M_Concrete':(190,190,185),'M_Glass':(120,180,220),'M_Wood':(170,120,70),'M_Water':(40,110,150),'M_Paving':(215,210,200),'M_Asphalt':(60,60,62)}
for n in ['M_Concrete','M_Glass','M_Wood','M_Water','M_Paving','M_Asphalt']:
    if d.Layers.FindByFullPath(n,-1)<0:
        L=Rhino.DocObjects.Layer(); L.Name=n; c=cols[n]; L.Color=System.Drawing.Color.FromArgb(c[0],c[1],c[2]); d.Layers.Add(L)
for vw in d.Views:
    if vw.ActiveViewport.Name=='Perspective':
        vw.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.FindByName('Shaded')
        d.Views.ActiveView=vw

# --- 1 地面・道路 ---
pav=path([('L',-1,-1),('L',22,-1),('L',22,20),('L',-4,20),('L',-4,2),('A',-1,2,3,180,270)])
add(ext(pav,-0.3,0.0),'M_Paving','Paving_Site')
road=path([('L',26,-7),('L',-1,-7),('A',-1,2,9,270,180),('L',-10,20),('L',-4,20),('L',-4,2),('A',-1,2,3,180,270),('L',26,-1)])
add(ext(road,-0.3,-0.12),'M_Asphalt','Road')

# --- 2 主ボリューム（左の箱7.5m＋右の箱6.8m） ---
left=path([('L',0,2.8),('L',12.6,2.8),('L',12.6,11.1),('L',2.0,11.1),('A',2.0,9.1,2.0,90,180),('L',0,2.8)])
right=path([('L',6.5,0),('L',13.8,0),('A',13.8,1.5,1.5,270,360),('L',15.3,10.1),('A',14.3,10.1,1.0,0,90),('L',6.0,11.1),('L',6.0,0.5),('A',6.5,0.5,0.5,180,270)])
u=union([ext(left,0,7.5),ext(right,0,6.8)])
add(u[0],'M_Concrete','Mass_Main')

# --- 3 凹み（右面x=7.0のみガラス、左面・奥はコンクリート、天井5.8m） ---
replace('Mass_Main',diff(get('Mass_Main').Geometry,[box(1.0,1.3,-0.1,7.25,6.8,5.8)]))
add(box(7.12,1.3,0.0,7.14,6.8,5.8),'M_Glass','Glass_Recess_RightFace')

# --- 4 スリット窓（左側面） ---
replace('Mass_Main',diff(get('Mass_Main').Geometry,[box(-0.1,3.2,0.3,0.2,4.5,5.8)]))
add(box(0.10,3.2,0.3,0.12,4.5,5.8),'M_Glass','Glass_Slit_Left')

# --- 5 正面の帯窓（丸い角R1.5を回る） ---
def band(x0,cx,cy,r,ro,ri):
    return path([('L',x0,cy-r-ro),('L',cx,cy-r-ro),('A',cx,cy,r+ro,270,360),('L',cx+r-ri,cy),('A',cx,cy,r-ri,360,270),('L',x0,cy-r+ri)])
replace('Mass_Main',diff(get('Mass_Main').Geometry,[ext(band(7.12,13.8,1.5,1.5,0.1,0.2),4.7,5.9)]))
add(ext(band(7.12,13.8,1.5,1.5,-0.08,0.10),4.7,5.9),'M_Glass','Glass_Ribbon_Front_Wrap')

# --- 6 裏の窓 ---
replace('Mass_Main',diff(get('Mass_Main').Geometry,[box(2.4,10.9,-0.1,6.8,11.2,2.4),box(8.0,10.9,4.7,12.0,11.2,5.9)]))
add(box(2.4,10.98,0.0,6.8,11.0,2.4),'M_Glass','Glass_Rear_1F_Sliding')
add(box(8.0,10.98,4.7,12.0,11.0,5.9),'M_Glass','Glass_Rear_2F_Ribbon')

# --- 7 木部 ---
ys=[1.3,2.675,4.05,5.425,6.8]
for i in range(len(ys)):
    y=ys[i]; y0=max(1.3,y-0.03); y1=min(6.8,y+0.03)
    if i==0: y1=1.36
    if i==len(ys)-1: y0=6.74
    add(box(7.0,y0,0.0,7.12,y1,5.77),'M_Wood','Wood_Mullion_Recess_%d'%i)
add(box(7.0,1.3,3.0,7.12,6.8,3.3),'M_Wood','Wood_FloorBand_Recess')
add(box(7.0,1.3,5.65,7.12,6.8,5.77),'M_Wood','Wood_HeadFrame_Recess')
sof=path([('L',1.0,2.8),('L',6.0,2.8),('L',6.0,1.3),('L',7.25,1.3),('L',7.25,6.8),('L',1.0,6.8)])
add(ext(sof,5.77,5.795),'M_Wood','Wood_Soffit_Recess')
for x in [9.4,11.7,13.8]:
    add(box(x-0.025,0.02,4.7,x+0.025,0.2,5.9),'M_Wood','Wood_Mullion_Ribbon_%.1f'%x)

# --- 8 車庫・1階だけの部分（3.3m） ---
one=ext(path([('L',12.6,0),('L',18.0,0),('L',18.0,10.1),('A',17.0,10.1,1.0,0,90),('L',12.6,11.1)]),0,3.3)
m2=union([get('Mass_Main').Geometry,one])[0]
gar=path([('L',11.3,-0.1),('L',17.3,-0.1),('L',17.3,9.76),('A',16.7,9.76,0.6,0,90),('L',13.2,10.36),('A',13.2,9.76,0.6,90,180),('L',12.6,1.3),('A',11.3,1.3,1.3,0,-90),('L',11.3,-0.1)])
replace('Mass_Main',diff(m2,[ext(gar,-0.1,2.7)]))

# --- 9 プール（画像から） ---
replace('Paving_Site',diff(get('Paving_Site').Geometry,[box(1.2,0.4,-0.25,5.8,4.5,0.1)]))
add(box(1.2,0.4,-0.17,5.8,4.5,-0.15),'M_Water','Water_Pool')

fin()
print(';'.join(LOG))
result = 'ok'
