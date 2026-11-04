# -*- coding: utf-8 -*-
# House massing from one exterior image (house_v6C.png) - RhinoCommon / IronPython, units mm
# Z up, street on -Y (front faces -Y), X to the right as seen from the street,
# origin = bottom-left-front corner of the building footprint (sharp corner of block A).
import Rhino, scriptcontext as sc, System, math
import Rhino.Geometry as G

d = sc.doc
d.ModelUnitSystem = Rhino.UnitSystem.Millimeters
d.ModelAbsoluteTolerance = 0.1
tol = d.ModelAbsoluteTolerance

# ---------------- parameters (see params.json) ----------------
A_W = 6000.0; DEPTH = 9000.0; A_H = 6000.0; A_R_BACKLEFT = 1200.0
PIER_W = 400.0                      # corner pier / left wall thickness
REC_D = 5200.0; REC_H = 5600.0      # recess depth (Y) and soffit height
B_X0 = 6000.0; B_LOW_X1 = 13400.0; B_SPLIT_Z = 4700.0
B_UP_X1 = 16400.0; B_H = 7400.0; B_R = 2000.0
GL_Z0 = 550.0; SLAB_Z0 = 2900.0; SLAB_Z1 = 3400.0; GLASS_Y0 = 200.0; GLASS_Y1 = 5000.0; POCKET_X = 1500.0
SLIT_Y0 = 400.0; SLIT_Y1 = 1400.0; SLIT_Z0 = 200.0; SLIT_Z1 = 5300.0
RIB_X0 = 7900.0; RIB_Z0 = 5000.0; RIB_Z1 = 6200.0; RIB_CUT = 250.0; RIB_GLASS_IN = 150.0
CP_X1 = 23000.0; CP_D = 7000.0; CP_Z0 = 4300.0; CP_Z1 = 4700.0; CP_PIER_X = 22000.0; WING_H = 2400.0
POOL_Y0 = -1200.0; POOL_R = 600.0; WATER_Z = -100.0
SIDEWALK_FRONT = 2000.0; SIDEWALK_LEFT = 1500.0; KERB_H = 150.0; KERB_R = 3500.0

# ---------------- helpers ----------------
def layer(n, rgb):
    i = d.Layers.FindByFullPath(n, -1)
    if i < 0:
        L = Rhino.DocObjects.Layer(); L.Name = n; L.Color = System.Drawing.Color.FromArgb(rgb[0], rgb[1], rgb[2])
        i = d.Layers.Add(L)
    return i
def add(b, lay, name):
    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = d.Layers.FindByFullPath(lay, -1); a.Name = name
    return d.Objects.AddBrep(b, a)
def box(x0, y0, z0, x1, y1, z1):
    return G.Box(G.BoundingBox(x0, y0, z0, x1, y1, z1)).ToBrep()
def arc(cx, cy, r, a0, a1, n=12):
    return [(cx + r*math.cos(math.radians(a0 + (a1-a0)*i/float(n))), cy + r*math.sin(math.radians(a0 + (a1-a0)*i/float(n)))) for i in range(n+1)]
def ext(pts, z0, z1):
    P = [G.Point3d(p[0], p[1], z0) for p in pts]; P.append(P[0])
    b = G.Surface.CreateExtrusion(G.PolylineCurve(P), G.Vector3d(0, 0, z1-z0)).ToBrep().CapPlanarHoles(tol)
    if b.SolidOrientation == G.BrepSolidOrientation.Inward: b.Flip()
    return b
def diff(b, cutters):
    for c in cutters:
        if b.SolidOrientation == G.BrepSolidOrientation.Inward: b.Flip()
        if c.SolidOrientation == G.BrepSolidOrientation.Inward: c.Flip()
        r = G.Brep.CreateBooleanDifference(b, c, tol)
        if r and len(r) > 0: b = r[0]
    return b

# ---------------- 1. reset, layers, view ----------------
for o in [o.Id for o in d.Objects]: d.Objects.Delete(o, True)
layer('M_Concrete', (170,170,165)); layer('M_Glass', (120,170,200)); layer('M_Wood', (170,115,60))
layer('M_Water', (40,90,120)); layer('M_Paving', (205,200,190)); layer('M_Asphalt', (60,60,62))
view = d.Views.Find('Perspective', False); d.Views.ActiveView = view
dm = Rhino.Display.DisplayModeDescription.FindByName('Shaded')
if dm: view.ActiveViewport.DisplayMode = dm

# ---------------- 2. ground & road ----------------
add(box(-12000, -12000, -250, 34000, 22000, -KERB_H), 'M_Asphalt', 'road asphalt')
kc = (-SIDEWALK_LEFT + KERB_R, -SIDEWALK_FRONT + KERB_R)
pave = [(kc[0], -SIDEWALK_FRONT), (26000, -SIDEWALK_FRONT), (26000, 13000), (-SIDEWALK_LEFT, 13000)] + arc(kc[0], kc[1], KERB_R, 180, 270)[:-1]
pool = [(PIER_W, REC_D)] + arc(PIER_W+POOL_R, POOL_Y0+POOL_R, POOL_R, 180, 270, 8) + arc(A_W-POOL_R, POOL_Y0+POOL_R, POOL_R, 270, 360, 8) + [(A_W, REC_D)]
add(diff(ext(pave, -KERB_H, 0), [ext(pool, -500, 50)]), 'M_Paving', 'lot and sidewalk paving (pool cut out)')
add(box(2500, -2700, -150, 34000, -2550, -145), 'M_Paving', 'road edge line front')
add(ext(arc(kc[0], kc[1], KERB_R+800, 180, 270) + arc(kc[0], kc[1], KERB_R+650, 270, 180), -150, -145), 'M_Paving', 'road edge line corner')
add(box(-2300, 1500, -150, -2150, 22000, -145), 'M_Paving', 'road edge line left')

# ---------------- 3-6. main volumes, recess, slit, ribbon ----------------
ptsA = [(0, 0), (A_W, 0), (A_W, DEPTH)] + arc(A_R_BACKLEFT, DEPTH-A_R_BACKLEFT, A_R_BACKLEFT, 90, 180)
A = ext(ptsA, 0, A_H)
A = diff(A, [box(PIER_W, -50, -50, A_W+50, REC_D, REC_H),                      # recess (courtyard) void
             box(-50, SLIT_Y0, SLIT_Z0, PIER_W+50, SLIT_Y1, SLIT_Z1)])         # slit window through corner wall
add(A, 'M_Concrete', 'A main volume')

pocket = box(B_X0-50, GLASS_Y0, GL_Z0, B_X0+POCKET_X, GLASS_Y1, REC_H)          # room behind recess glass
door = box(B_LOW_X1-200, 4000, 0, B_LOW_X1+50, 5000, 2200)                     # hidden side: entrance under carport
Blow = diff(ext([(B_X0, 0), (B_LOW_X1, 0), (B_LOW_X1, DEPTH), (B_X0, DEPTH)], 0, B_SPLIT_Z), [pocket, door])
add(Blow, 'M_Concrete', 'B lower volume')

bc = (B_UP_X1 - B_R, B_R)   # centre of the front-right corner arc
def band(r_out, r_in, x0, yend, z0, z1):
    outer = [(x0, bc[1]-r_out)] + arc(bc[0], bc[1], r_out, 270, 360) + [(bc[0]+r_out, yend)]
    inner = [(bc[0]+r_in, yend)] + arc(bc[0], bc[1], r_in, 360, 270) + [(x0, bc[1]-r_in)]
    return ext(outer + inner, z0, z1)
ptsB = [(B_X0, 0)] + arc(bc[0], bc[1], B_R, 270, 360) + [(B_UP_X1, DEPTH), (B_X0, DEPTH)]
Bup = diff(ext(ptsB, B_SPLIT_Z, B_H), [pocket, band(B_R+100, B_R-RIB_CUT, RIB_X0, B_R+300, RIB_Z0, RIB_Z1)])
add(Bup, 'M_Concrete', 'B upper volume')

add(box(B_X0, GLASS_Y0, SLAB_Z0, B_X0+POCKET_X, GLASS_Y1, SLAB_Z1), 'M_Concrete', 'B 1F slab in pocket')
add(box(B_X0, GLASS_Y0, GL_Z0, B_X0+20, GLASS_Y1, SLAB_Z0), 'M_Glass', 'recess glass GF')
add(box(B_X0, GLASS_Y0, SLAB_Z1, B_X0+20, GLASS_Y1, REC_H), 'M_Glass', 'recess glass 1F')
add(box(PIER_W/2-10, SLIT_Y0, SLIT_Z0, PIER_W/2+10, SLIT_Y1, SLIT_Z1), 'M_Glass', 'slit window reeded glass')
add(band(B_R-RIB_GLASS_IN, B_R-RIB_GLASS_IN-20, RIB_X0, B_R+300, RIB_Z0, RIB_Z1), 'M_Glass', 'ribbon window glass')
straight = bc[0] - RIB_X0
for k in range(1, 5):
    x = RIB_X0 + straight*k/4.0 if k < 4 else bc[0] - 200
    add(box(x-25, 140, RIB_Z0, x+25, 260, RIB_Z1), 'M_Glass', 'ribbon mullion')
mp = arc(bc[0], bc[1], B_R-160, 315, 315, 1)[0]
m = box(-25, -60, RIB_Z0, 25, 60, RIB_Z1); m.Rotate(math.radians(45), G.Vector3d.ZAxis, G.Point3d.Origin); m.Translate(G.Vector3d(mp[0], mp[1], 0))
add(m, 'M_Glass', 'ribbon mullion (corner)')

# ---------------- 7. timber ----------------
bay = (GLASS_Y1 - GLASS_Y0) / 4.0
for k in range(5):
    y = GLASS_Y0 + bay*k; y0 = max(GLASS_Y0, y-60); y1 = min(GLASS_Y1, y+60)
    add(box(B_X0-60, y0, GL_Z0, B_X0+60, y1, SLAB_Z0), 'M_Wood', 'timber mullion GF')
    add(box(B_X0-60, y0, SLAB_Z1, B_X0+60, y1, REC_H), 'M_Wood', 'timber mullion 1F')
add(box(B_X0-50, GLASS_Y0, SLAB_Z0, B_X0+60, GLASS_Y1, SLAB_Z1), 'M_Wood', 'timber band at 1F slab')
add(box(B_X0-50, GLASS_Y0, GL_Z0, B_X0+60, GLASS_Y1, GL_Z0+100), 'M_Wood', 'timber sill')
add(box(B_X0-50, GLASS_Y0, REC_H-100, B_X0+60, GLASS_Y1, REC_H), 'M_Wood', 'timber head')
add(box(B_X0+20, GLASS_Y0, SLAB_Z0-50, B_X0+POCKET_X, GLASS_Y1, SLAB_Z0), 'M_Wood', 'timber ceiling GF (interior soffit)')
add(box(B_X0+20, GLASS_Y0, REC_H-50, B_X0+POCKET_X, GLASS_Y1, REC_H), 'M_Wood', 'timber ceiling 1F (interior soffit)')

# ---------------- 8. carport / canopy ----------------
add(box(B_LOW_X1, 0, CP_Z0, CP_X1, CP_D, CP_Z1), 'M_Concrete', 'carport canopy slab')
add(box(B_LOW_X1, CP_D-300, 0, CP_PIER_X+300, CP_D, CP_Z0), 'M_Concrete', 'carport back wall')
add(box(CP_PIER_X, 3000, 0, CP_PIER_X+300, CP_D-300, CP_Z0), 'M_Concrete', 'carport right wall (pier)')
add(box(CP_PIER_X, 0, 0, CP_PIER_X+300, 3000, WING_H), 'M_Concrete', 'carport low wing wall')
add(box(B_LOW_X1, 0, 0, CP_PIER_X, CP_D-300, 20), 'M_Paving', 'carport floor pad')

# ---------------- 9. pool ----------------
add(ext(pool, -500, -450), 'M_Concrete', 'pool basin floor')
add(ext(pool, WATER_Z-20, WATER_Z), 'M_Water', 'pool water surface')

# ---------------- 10. hidden back / right side ----------------
add(box(B_LOW_X1-200, 4000, 0, B_LOW_X1-150, 5000, 2200), 'M_Wood', 'entrance door (hidden side, assumed)')

view.ActiveViewport.ZoomExtents()
d.Views.Redraw()
result = 'ok'
