# -*- coding: utf-8 -*-
# 比較用：模型スクリプトを実行 → 地面・道路を共通のものに差し替え → 素材を共通で付ける → 同じカメラで撮る
# 呼ぶ前に MODEL, TAG, ALIGN, WALLS を globals に入れる（run() を呼ぶ）
import Rhino, System, io, os
import Rhino.Geometry as G
B = 'C:/path/to/kit/'
TP = B + 'texture_patterns/m/'
WOOD = B + 'model_v12/materials/wood/'
TX = B + 'compare/tex/'   # make_tex.py：打放しは少し暗く、黒モルタルは凹凸を弱め大きく貼る
TEX = {'concrete': (TX + 'concrete/', 1800), 'black_mortar': (TX + 'black_mortar/', 2400), 'rammed_earth': (TX + 'rammed_earth/', 1500), 'concrete_v6': (TX + 'concrete_v6/', 14400)}  # concrete_v6：外観 v6 に寄せた明るいグレー、14.4m 角でリピートを消す（tex_v6/make_concrete_v6.py）
TT = Rhino.DocObjects.TextureType
YF = -1800

def doc(): return Rhino.RhinoDoc.ActiveDoc

def layer(name, rgb):
    d = doc(); i = d.Layers.FindByFullPath(name, -1)
    if i < 0:
        L = Rhino.DocObjects.Layer(); L.Name = name; i = d.Layers.Add(L)
    L = d.Layers[i]; L.Color = System.Drawing.Color.FromArgb(*rgb); d.Layers.Modify(L, i, True)
    return i

def mat_for(li, rgb, transp=0.0, refl=0.0, base=None):
    d = doc(); m = Rhino.DocObjects.Material(); m.Name = d.Layers[li].Name
    m.DiffuseColor = System.Drawing.Color.FromArgb(*rgb); m.Transparency = transp; m.Reflectivity = refl
    if transp > 0: m.TransparentColor = System.Drawing.Color.FromArgb(*rgb)
    mi = d.Materials.Add(m)
    if base:
        m = d.Materials[mi]
        for f, t in (('basecolor', TT.PBR_BaseColor), ('normal', TT.Bump), ('roughness', TT.PBR_Roughness),
                     ('ao', TT.PBR_AmbientOcclusion), ('metallic', TT.PBR_Metallic)):
            if os.path.exists(base + f + '.png'):
                tx = Rhino.DocObjects.Texture(); tx.FileName = base + f + '.png'; tx.Enabled = True; m.SetTexture(tx, t)
        if not os.path.exists(base + 'roughness.png'):
            m.SetBitmapTexture(base + 'basecolor.png'); m.SetBumpTexture(base + 'normal.png')
        m.CommitChanges(); d.Materials.Modify(m, mi, True)
    L = d.Layers[li]; L.RenderMaterialIndex = mi; d.Layers.Modify(L, li, True)
    return mi

def objs(li):
    d = doc(); return list(d.Objects.FindByLayer(d.Layers[li]) or [])

def remap(li, s):
    d = doc(); mp = Rhino.Render.TextureMapping.CreateBoxMapping(G.Plane.WorldXY, G.Interval(0, s), G.Interval(0, s), G.Interval(0, s), True)
    for o in objs(li):
        a = o.Attributes.Duplicate(); a.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
        d.Objects.ModifyAttributes(o, a, True); d.Objects.ModifyTextureMapping(o.Id, 1, mp)

def run(MODEL, TAG, ALIGN=False, WALLS=('concrete',)):
    d = doc()
    ns = {}
    exec(io.open(MODEL, encoding='utf-8').read(), ns)
    OUT = B + 'compare/' + TAG + '/'
    if not os.path.isdir(OUT): os.makedirs(OUT)
    # 地面・道路・水盤の底は共通のものに差し替える
    for ln in ('M_Paving', 'M_Asphalt', 'M_BasinStone'):
        i = d.Layers.FindByFullPath(ln, -1)
        if i >= 0:
            for o in objs(i): d.Objects.Delete(o, True)
    LC = layer('M_Concrete', (205, 203, 198))
    bb = G.BoundingBox.Empty
    for o in objs(LC): bb.Union(o.Geometry.GetBoundingBox(True))
    if ALIGN:   # 画像だけの模型は原点が分からないので、建物の左端・一番前・地面を正解(v14)にそろえる
        xf = G.Transform.Translation(-bb.Min.X, YF - bb.Min.Y, 0)   # 高さは地面=0 のまま
        for o in list(d.Objects):
            if o.ObjectType == Rhino.DocObjects.ObjectType.Brep or o.ObjectType == Rhino.DocObjects.ObjectType.Extrusion or o.ObjectType == Rhino.DocObjects.ObjectType.Mesh:
                d.Objects.Transform(o, xf, True)
        bb.Transform(xf)
    LP = layer('M_Paving', (190, 188, 182)); LR = layer('M_Asphalt', (70, 70, 72))
    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = LP
    d.Objects.AddBrep(G.Box(G.BoundingBox(G.Point3d(-8000, -3000, -250), G.Point3d(26000, 16000, -200))).ToBrep(), a)
    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = LR
    d.Objects.AddBrep(G.Box(G.BoundingBox(G.Point3d(-30000, -30000, -300), G.Point3d(40000, -3000, -250))).ToBrep(), a)
    # 共通の素材
    mat_for(LP, (190, 188, 182)); mat_for(LR, (70, 70, 72))
    LG = layer('M_Glass', (60, 80, 90)); mat_for(LG, (60, 80, 90), 0.55, 0.35)
    LW = layer('M_Water', (40, 60, 66)); mat_for(LW, (40, 60, 66), 0.7, 0.5)
    for ln in ('M_Wood', 'M_Frame'):
        li = layer(ln, (196, 150, 98)); mat_for(li, (196, 150, 98), base=WOOD); remap(li, 1200)
    for ln in ('M_Interior',):
        i = d.Layers.FindByFullPath(ln, -1)
        if i >= 0: mat_for(i, (150, 140, 128))
    v = d.Views.Find('Perspective', False); d.Views.ActiveView = v; vp = v.ActiveViewport
    def shot(name, cam, tgt, lens=30, parallel=False, mode='Rendered', w=1600, h=900, up=(0, 0, 1)):
        if parallel: vp.ChangeToParallelProjection(True)
        else: vp.ChangeToPerspectiveProjection(True, lens)
        vp.SetCameraLocations(G.Point3d(*tgt), G.Point3d(*cam)); vp.CameraUp = G.Vector3d(*up)
        if not parallel: vp.Camera35mmLensLength = lens
        vp.DisplayMode = Rhino.Display.DisplayModeDescription.FindByName(mode)
        if parallel: vp.ZoomBoundingBox(G.BoundingBox(G.Point3d(-2000, -4000, -300), G.Point3d(20000, 11500, 8500))); vp.Magnify(0.62, False)
        v.Redraw(); Rhino.RhinoApp.Wait()
        c = Rhino.Display.ViewCapture(); c.Width = w; c.Height = h; c.DrawAxes = False; c.DrawGrid = False; c.DrawGridAxes = False
        c.CaptureToBitmap(v).Save(OUT + name, System.Drawing.Imaging.ImageFormat.Png)
    shots = []
    for wname in WALLS:
        base, s = TEX[wname]; mat_for(LC, (205, 203, 198), base=base); remap(LC, s)
        shot('eye_%s.png' % wname, (-8256, -9408, 1610), (8500, 3200, 2600)); shots.append(wname)
        if wname == WALLS[0]:
            shot('back.png', (28000, 22000, 9000), (9000, 4000, 2500))
            shot('back_left.png', (-4000, 30000, 6000), (7500, 6000, 3000))
            shot('right_front.png', (22000, -14000, 4500), (12000, 0, 4800))
            shot('axo.png', (-14000, -20000, 16000), (9000, 3800, 2000), parallel=True)
    # 形の比較用（地面を隠して、平面・正面・右側面を平行投影の Shaded で撮る）
    for ln in ('M_Paving', 'M_Asphalt', 'M_Water'):
        i = d.Layers.FindByFullPath(ln, -1)
        if i >= 0:
            for o in objs(i): d.Objects.Hide(o, True)
    shot('sil_top.png', (9000, 4000, 60000), (9000, 4000, 0), parallel=True, mode='Shaded', w=1400, h=1000, up=(0, 1, 0))
    shot('sil_front.png', (9000, -60000, 3500), (9000, 0, 3500), parallel=True, mode='Shaded', w=1400, h=1000)
    shot('sil_right.png', (60000, 4000, 3500), (0, 4000, 3500), parallel=True, mode='Shaded', w=1400, h=1000)
    shot('sil_back.png', (9000, 60000, 3500), (9000, 0, 3500), parallel=True, mode='Shaded', w=1400, h=1000)
    d.Objects.ShowAll(True) if hasattr(d.Objects, 'ShowAll') else None
    d.WriteFile(OUT + 'model.3dm', Rhino.FileIO.FileWriteOptions())
    return 'ok %s bb=(%d,%d,%d)-(%d,%d,%d)' % (TAG, bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z)
