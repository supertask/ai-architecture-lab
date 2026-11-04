# -*- coding: utf-8 -*-
# v13 の図面（draw_v14.py の数字）＋外観 v6 の窓と仕上げ。単位 mm。テクスチャは materials/（Qwen-Image 2.1 → DeepBump → make_pbr）
import Rhino, System, math
import Rhino.Geometry as G
d = Rhino.RhinoDoc.ActiveDoc
tol = d.ModelAbsoluteTolerance
for o in list(d.Objects):
    d.Objects.Delete(o, True)
MAT = 'C:/path/to/kit/model_v12/materials/'
OUT = 'C:/path/to/kit/model_v14/'
DEP, R_BACK, SW, REC_Y, GX, YF, R_FL = 9300, 2000, 1000, 5000, 7000, -1800, 900
PIER_Y, EXT_TOP, SL0, SL1 = 1000, -500, 1400, 2700   # v14：柱・凹みの上の屋根・スリットを 1m 前へ（描き込み r9）
EX, R_EX, X_HI = 6000, 500, 12600
G0, G1, GB, R_G, R_GF = 12600, 17300, 8600, 650, 1300
BX1, R_BR, X2, R_2F = 18000, 1200, 15300, 1500
H_L, H_R, H_REC, H_CP, H_1F, SLIT_TOP = 7500, 6800, 5800, 2700, 3300, 5800
FL2, FL2T = 2750, 3150   # 2階の床（下端・上端）

def arc(cx, cy, r, a0, a1, n=16):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / float(n))), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / float(n)))) for i in range(n + 1)]
def prism(pts, z0, z1):
    P = [G.Point3d(x, y, z0) for x, y in pts]
    if P[0].DistanceTo(P[-1]) > 1: P.append(P[0])
    crv = G.PolylineCurve(P)
    if crv.ClosedCurveOrientation(G.Vector3d.ZAxis) == G.CurveOrientation.Clockwise: crv.Reverse()
    return G.Extrusion.Create(crv, z1 - z0, True).ToBrep()
def box(x0, y0, z0, x1, y1, z1):
    return G.Box(G.BoundingBox(G.Point3d(min(x0, x1), min(y0, y1), min(z0, z1)), G.Point3d(max(x0, x1), max(y0, y1), max(z0, z1)))).ToBrep()
def diff(a, bs):
    cur = [a]
    for b in bs:
        nxt = []
        for c in cur:
            r = G.Brep.CreateBooleanDifference(c, b, tol)
            nxt += list(r) if r else [c]
        cur = nxt
    return cur
def material(name, rgb, tex=None, transp=0.0, refl=0.0, shine=0.0):
    m = Rhino.DocObjects.Material(); m.Name = name
    m.DiffuseColor = System.Drawing.Color.FromArgb(*rgb)
    m.Transparency = transp; m.Reflectivity = refl; m.Shine = shine
    if transp > 0: m.TransparentColor = System.Drawing.Color.FromArgb(*rgb)
    if tex:
        m.SetBitmapTexture(MAT + tex + '/basecolor.png')
        m.SetBumpTexture(MAT + tex + '/normal.png')
    return d.Materials.Add(m)
def layer(name, rgb, mi):
    i = d.Layers.FindByFullPath(name, -1)   # 同じ名前のレイヤーが既にあると Add は -1 を返す（v13 初回で素材が全部外れた）
    if i < 0:
        L = Rhino.DocObjects.Layer(); L.Name = name; i = d.Layers.Add(L)
    L = d.Layers[i]; L.Color = System.Drawing.Color.FromArgb(*rgb); L.RenderMaterialIndex = mi
    d.Layers.Modify(L, i, True)
    return i
SC = {}
def mk(name, rgb, tex=None, scale=1000, **kw):
    li = layer(name, rgb, material(name, rgb, tex, **kw)); SC[li] = scale; return li
L_CON = mk('M_Concrete', (205, 203, 198), 'concrete', 1800)
L_WOOD = mk('M_Wood', (196, 150, 98), 'wood', 1200)
L_GL = mk('M_Glass', (60, 80, 90), transp=0.55, refl=0.35, shine=0.9)
L_FR = mk('M_Frame', (214, 160, 96), 'wood', 1200)
L_WATER = mk('M_Water', (40, 60, 66), transp=0.7, refl=0.5, shine=1.0)
L_BAS = mk('M_BasinStone', (40, 40, 42), 'basin', 1200)
L_PAV = mk('M_Paving', (190, 188, 182), 'paving', 2000)
L_ROAD = mk('M_Asphalt', (70, 70, 72))
L_INT = mk('M_Interior', (150, 140, 128))
def add(brep, li, name):
    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = li; a.Name = name
    a.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
    g = d.Objects.AddBrep(brep, a)
    s = SC[li]
    mp = Rhino.Render.TextureMapping.CreateBoxMapping(G.Plane.WorldXY, G.Interval(0, s), G.Interval(0, s), G.Interval(0, s), True)
    d.Objects.ModifyTextureMapping(g, 1, mp)
    return g
# 形
garage = [(G0 - R_GF, YF - 10)] + arc(G0 - R_GF, YF + R_GF, R_GF, -90, 0)[1:] + [(G0, GB - R_G)] + arc(G0 + R_G, GB - R_G, R_G, 180, 90)[1:] + [(G1 - R_G, GB)] + arc(G1 - R_G, GB - R_G, R_G, 90, 0)[1:] + [(G1, YF - 10)]
gv = prism(garage, -10, H_CP)
# 左の箱（黄）：左の柱 x0〜1 は y=2m から。凹みの奥（y≥5m）は全部の高さ。凹みの上の屋根 x1〜6・y2〜5・5.8〜7.5。右の箱の上の帯 x6〜12.6・y2〜9.3・6.8〜7.5
left = [(0, PIER_Y), (SW, PIER_Y), (SW, REC_Y), (GX, REC_Y), (GX, DEP), (R_BACK, DEP)] + arc(R_BACK, DEP - R_BACK, R_BACK, 90, 180)[1:]
Lb = diff(prism(left, 0, H_L), [box(1200, REC_Y + 200, 0, 6800, 8800, 5500), box(-10, SL0, 300, 150, SL1, SLIT_TOP)])
Lroof = box(SW, PIER_Y, H_REC, EX, REC_Y, H_L)
Lband = box(EX, PIER_Y, H_R, X_HI, DEP, H_L)
# 右の箱（灰）6.8m：前の左角の出っ張り x6〜7（奥 y=-0.5、前の左角 R0.5）、右前の角 R1.5 は 3.3m より上だけ
right = [(GX, EXT_TOP), (EX, EXT_TOP)] + arc(EX + R_EX, YF + R_EX, R_EX, 180, 270)[1:] + [(X2 - R_2F, YF)] + arc(X2 - R_2F, YF + R_2F, R_2F, -90, 0)[1:] + arc(X2 - R_2F, DEP - R_2F, R_2F, 0, 90) + [(GX, DEP)]   # 右奥の角も R1.5（3.3m より上、本人 2026-11-04）
Rb = diff(prism(right, 0, H_R), [gv, box(GX - 10, EXT_TOP + 150, 0, 10800, REC_Y, 5500)])
Rroof = box(EX, EXT_TOP, H_REC, GX, REC_Y, H_R)     # 凹みの上の屋根（x6〜7）。v13 は y=PIER_Y までで、その奥 5.8〜6.8m に隙間があった
one = [(X2 - R_2F, YF), (BX1, YF)] + arc(BX1 - R_BR, DEP - R_BR, R_BR, 0, 90) + [(X2, DEP), (X2, YF + R_2F)]
Ob = diff(prism(one, 0, H_1F), [prism(garage, -10, H_CP)])
Ob.append(box(X2 - R_2F, DEP - R_2F, 0, X2, DEP, H_1F))   # 右奥の丸い角の下（1階は四角）
# 窓（2026-11-04）：正面の2階の帯窓（外観 v6C）、裏の 1階 LDK の掃き出し窓・2階の帯窓（本人「やって大丈夫」、仮の値）
RIB0, RZ0, RZ1, DPT = EX + R_EX + 600, 4700, 5900, 300
rib_out = [(RIB0, YF - 100), (X2 - R_2F, YF - 100)] + arc(X2 - R_2F, YF + R_2F, R_2F + 100, -90, 0)[1:]
rib_in = arc(X2 - R_2F, YF + R_2F, R_2F - DPT, 0, -90) + [(RIB0, YF + DPT)]
rib_cut = prism(rib_out + rib_in, RZ0, RZ1)
g_out = [(RIB0, YF + 140), (X2 - R_2F, YF + 140)] + arc(X2 - R_2F, YF + R_2F, R_2F - 140, -90, 0)[1:]
g_in = arc(X2 - R_2F, YF + R_2F, R_2F - 160, 0, -90) + [(RIB0, YF + 160)]
BK1 = (2400, 6800, 0, 2400)       # 裏・1階 LDK の掃き出し窓 x, z
BK2 = (8000, 12000, RZ0, RZ1)     # 裏・2階の帯窓（正面と同じ高さ）
Lb = diff(Lb[0], [box(BK1[0], DEP - DPT, BK1[2], BK1[1], DEP + 10, BK1[3])]) + Lb[1:]
Rb = diff(Rb[0], [rib_cut, box(BK2[0], DEP - DPT, BK2[2], BK2[1], DEP + 10, BK2[3])]) + Rb[1:]
add(prism(g_out + g_in, RZ0, RZ1), L_GL, '正面の帯窓のガラス')
for xx in (9400, 11700, X2 - R_2F):
    add(box(xx - 30, YF + 100, RZ0, xx + 30, YF + 200, RZ1), L_FR, '帯窓の方立')
add(box(BK1[0], DEP - 160, BK1[2], BK1[1], DEP - 140, BK1[3]), L_GL, '裏の掃き出し窓')
add(box(BK2[0], DEP - 160, BK2[2], BK2[1], DEP - 140, BK2[3]), L_GL, '裏の帯窓')
for b in Lb: add(b, L_CON, '左の箱')
add(Lroof, L_CON, '左の箱・凹みの上の屋根'); add(Lband, L_CON, '左の箱・上の帯')
for b in Rb: add(b, L_CON, '右の箱')
add(Rroof, L_CON, '右の箱・凹みの上の屋根')
for b in Ob: add(b, L_CON, '1階だけの部分')
# 部屋の床・2階の床・木の天井
for (x0, y0, x1, y1) in ((1200, REC_Y, 6800, 8800), (GX, EXT_TOP + 150, 10800, REC_Y)):
    add(box(x0, y0, FL2, x1, y1, FL2T), L_CON, '2階の床')
    add(box(x0, y0, FL2 - 40, x1, y1, FL2), L_WOOD, '1階の木の天井')
    add(box(x0, y0, 5460, x1, y1, 5500), L_WOOD, '2階の木の天井')
    add(box(x0, y0, -10, x1, y1, 0), L_INT, '床')
# 凹みの奥（y=5m）は壁（図面「凹みの奥の壁」、青線なし）。v12〜v14 初版はここをガラスにしていた（本人指摘 2026-11-04）
# 凹みの横（x=7m）のガラス
add(box(GX - 140, EXT_TOP + 150, FL2, GX - 20, REC_Y, FL2T + 60), L_WOOD, '横の木の帯')
for z0, z1 in ((0, FL2), (FL2T + 60, H_REC)):
    add(box(GX - 12, EXT_TOP + 150, z0, GX, REC_Y, z1), L_GL, '凹みの横のガラス')
for y in (EXT_TOP + 150, 1300, 2700, 4000, REC_Y - 60):
    add(box(GX - 140, y - 60, 0, GX, y + 60, H_REC), L_FR, '方立')
add(box(140, SL0, 300, 150, SL1, SLIT_TOP), L_GL, 'スリットのガラス')
# 地面・水盤（凹み＋前 1.8m）・道路
basin = [(0, YF), (EX, YF), (EX, EXT_TOP), (GX, EXT_TOP), (GX, REC_Y), (SW, REC_Y), (SW, PIER_Y), (0, PIER_Y)]
for b in diff(box(-8000, -3000, -200, 26000, 16000, 0), [prism(basin, -150, 10)]): add(b, L_PAV, '歩道')
add(prism(basin, -200, -150), L_BAS, '水盤の底')
add(prism(basin, -60, -40), L_WATER, '水面')
add(box(-30000, -30000, -260, 40000, -3000, -60), L_ROAD, '道路')
# 太陽（夕方、v6 と同じく左手前から低く）
sun = d.Lights.Sun
try:
    sun.ManualControlOn = True
except Exception:
    pass
try:
    sun.Enabled = True; sun.Altitude = 22.0; sun.Azimuth = 235.0
except Exception as e:
    pass
d.Views.Redraw()
d.WriteFile(OUT + 'massing_v14.3dm', Rhino.FileIO.FileWriteOptions())
result = 'objs %d L%d R%d O%d' % (len(list(d.Objects)), len(Lb), len(Rb), len(Ob))
