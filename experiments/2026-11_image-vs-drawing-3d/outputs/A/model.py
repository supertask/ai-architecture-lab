# -*- coding: utf-8 -*-
# A_image_only : massing model inferred from ONE exterior perspective image.
# Units: mm. Z up. Street on -Y side. X to the right as seen from street.
# Origin = front-left corner of the tall left volume (nearest vertical corner in the image).
# All dimensions: see params.json (estimated via 2-point perspective, eye height ~2.1 m).
import Rhino
import Rhino.Geometry as G
import System
import math

d = Rhino.RhinoDoc.ActiveDoc
tol = d.ModelAbsoluteTolerance if d.ModelAbsoluteTolerance > 0 else 0.1

# ---------------------------------------------------------------- reset
ids = [o.Id for o in d.Objects]
for i in ids:
    d.Objects.Delete(i, True)

# ---------------------------------------------------------------- layers
LAYER_COLORS = {
    "M_Concrete": System.Drawing.Color.FromArgb(190, 188, 182),
    "M_Glass": System.Drawing.Color.FromArgb(120, 170, 200),
    "M_Wood": System.Drawing.Color.FromArgb(170, 120, 70),
    "M_Water": System.Drawing.Color.FromArgb(40, 90, 120),
    "M_Paving": System.Drawing.Color.FromArgb(215, 212, 205),
    "M_Asphalt": System.Drawing.Color.FromArgb(70, 70, 72),
}


def layer_index(name):
    idx = d.Layers.FindByFullPath(name, -1)
    if idx < 0:
        idx = d.Layers.Add(name, LAYER_COLORS.get(name, System.Drawing.Color.Gray))
    return idx


def attrs(layer):
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = layer_index(layer)
    return a


def add(brep, layer):
    if brep is None:
        return None
    return d.Objects.AddBrep(brep, attrs(layer))


# ---------------------------------------------------------------- geometry helpers
def box(x0, y0, z0, x1, y1, z1):
    bb = G.BoundingBox(G.Point3d(min(x0, x1), min(y0, y1), min(z0, z1)),
                       G.Point3d(max(x0, x1), max(y0, y1), max(z0, z1)))
    return G.Box(bb).ToBrep()


def arc_pts(cx, cy, r, a0, a1, n=8):
    # points on an arc from angle a0 to a1 (degrees), inclusive
    pts = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * float(k) / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rrect_pts(x0, y0, x1, y1, rfl=0.0, rfr=0.0, rbr=0.0, rbl=0.0):
    # rectangle in plan with optional rounded corners (fl = front-left = (x0,y0), counter-clockwise)
    pts = []
    if rfl > 0:
        pts += arc_pts(x0 + rfl, y0 + rfl, rfl, 180, 270)
    else:
        pts.append((x0, y0))
    if rfr > 0:
        pts += arc_pts(x1 - rfr, y0 + rfr, rfr, 270, 360)
    else:
        pts.append((x1, y0))
    if rbr > 0:
        pts += arc_pts(x1 - rbr, y1 - rbr, rbr, 0, 90)
    else:
        pts.append((x1, y1))
    if rbl > 0:
        pts += arc_pts(x0 + rbl, y1 - rbl, rbl, 90, 180)
    else:
        pts.append((x0, y1))
    return pts


def prism(pts, z0, z1):
    # extrude closed plan polyline (list of (x,y)) from z0 to z1 -> closed Brep
    clean = []
    for p in pts:
        if not clean or (abs(clean[-1][0] - p[0]) > 1e-6 or abs(clean[-1][1] - p[1]) > 1e-6):
            clean.append(p)
    if abs(clean[0][0] - clean[-1][0]) < 1e-6 and abs(clean[0][1] - clean[-1][1]) < 1e-6:
        clean = clean[:-1]
    pl = G.Polyline()
    for p in clean:
        pl.Add(G.Point3d(p[0], p[1], z0))
    pl.Add(G.Point3d(clean[0][0], clean[0][1], z0))
    crv = pl.ToNurbsCurve()
    srf = G.Surface.CreateExtrusion(crv, G.Vector3d(0, 0, z1 - z0))
    b = srf.ToBrep()
    capped = b.CapPlanarHoles(tol)
    # [Hermes 実行時の修正 2026-11-04] 面の向きが内向きのソリッドになり、ブール演算で壁が消えていた。形の数値は変えない。
    if capped is not None and capped.SolidOrientation == G.BrepSolidOrientation.Inward:
        capped.Flip()
    return capped if capped is not None else b


def diff(a, cutters):
    if not isinstance(cutters, list):
        cutters = [cutters]
    cur = a
    for c in cutters:
        r = G.Brep.CreateBooleanDifference(cur, c, tol)
        if r is not None and len(r) > 0:
            # keep the largest piece
            best = r[0]
            for b in r:
                if b.GetVolume() > best.GetVolume():
                    best = b
            cur = best
    return cur


def union(breps):
    lst = System.Collections.Generic.List[G.Brep]()
    for b in breps:
        lst.Add(b)
    r = G.Brep.CreateBooleanUnion(lst, tol)
    if r is not None and len(r) > 0:
        return list(r)
    return breps


# ---------------------------------------------------------------- parameters (mm)
# left tall volume (L)
L_X0, L_X1 = 0.0, 3930.0
L_Y0, L_Y1 = 0.0, 7000.0
L_H = 6400.0
L_R_BACKLEFT = 600.0          # rounded far corner seen at left end of side face
# right lower volume (R), projects towards the street
R_X0, R_X1_UP, R_X1_GF = 3170.0, 12500.0, 9400.0
R_Y0, R_Y1 = -2330.0, 7000.0
R_H = 6000.0
R_GF_TOP = 3600.0             # underside of cantilevered upper floor
R_R_FL = 350.0                # rounded front-left corner (both floors)
R_R_FR_UP = 1500.0            # big rounded front-right corner, upper floor
R_R_FR_GF = 300.0             # small round at ground-floor wall end
PARAPET_T = 200.0
PARAPET_H = 300.0
# recess (double-height loggia) in L, next to R
REC_X0, REC_X1 = 360.0, R_X0
REC_Y1 = 2130.0               # recess back wall (concrete)
REC_TOP = 5440.0              # soffit level
# glazed wall = R/L side face at X=R_X0, from Y=-1950 to REC_Y1
GL_Y0, GL_Y1 = -1950.0, REC_Y1
GL_Z0, GL_Z1 = 0.0, 5000.0
GL_REVEAL = 150.0
BAND_Z0, BAND_Z1 = 2750.0, 3150.0
# slit window on the left face (X=0)
SL_Y0, SL_Y1 = 400.0, 1500.0
SL_Z0, SL_Z1 = 300.0, 5500.0
SL_REVEAL = 250.0
# ribbon window on R upper floor
RB_X0 = 4180.0
RB_Z0, RB_Z1 = 4230.0, 5300.0
RB_REVEAL = 250.0
# carport
CP_X0, CP_X1 = 12300.0, 18300.0
CP_Y0, CP_Y1 = -3600.0, 4200.0
CP_Z0, CP_Z1 = 3300.0, R_GF_TOP
# site
GROUND_T = 150.0              # paving thickness / kerb height
PAVE_X0, PAVE_X1 = -1800.0, 30000.0
PAVE_Y0, PAVE_Y1 = -4000.0, 20000.0
PAVE_CORNER_R = 2000.0
ROAD_W = 7000.0
POOL_X0, POOL_Y0 = -400.0, -1800.0
WATER_Z = -80.0

# ---------------------------------------------------------------- L volume
L = prism(rrect_pts(L_X0, L_Y0, L_X1, L_Y1, rbl=L_R_BACKLEFT), 0.0, L_H)
L_roofcut = prism(rrect_pts(L_X0 + PARAPET_T, L_Y0 + PARAPET_T, L_X1 - PARAPET_T, L_Y1 - PARAPET_T,
                            rbl=L_R_BACKLEFT - PARAPET_T), L_H - PARAPET_H, L_H + 100.0)
recess = box(REC_X0, -500.0, -300.0, REC_X1, REC_Y1, REC_TOP)
slit = box(-100.0, SL_Y0, SL_Z0, SL_REVEAL, SL_Y1, SL_Z1)
glz_open_L = box(R_X0 - 1.0, 0.0, GL_Z0, R_X0 + GL_REVEAL, GL_Y1, GL_Z1)
L = diff(L, [L_roofcut, recess, slit, glz_open_L])
add(L, "M_Concrete")

# ---------------------------------------------------------------- R volume (ground floor + upper floor)
R_gf = prism(rrect_pts(R_X0, R_Y0, R_X1_GF, R_Y1, rfl=R_R_FL, rfr=R_R_FR_GF), 0.0, R_GF_TOP)
# hidden: rooms behind carport (simple guess)
R_gf_back = box(R_X1_GF - 10.0, CP_Y1, 0.0, R_X1_UP, R_Y1, R_GF_TOP)
R_up = prism(rrect_pts(R_X0, R_Y0, R_X1_UP, R_Y1, rfl=R_R_FL, rfr=R_R_FR_UP), R_GF_TOP - 10.0, R_H)
Rs = union([R_gf, R_gf_back, R_up])
R = Rs[0]
if len(Rs) > 1:
    for extra in Rs[1:]:
        add(extra, "M_Concrete")

R_roofcut = prism(rrect_pts(R_X0 + PARAPET_T, R_Y0 + PARAPET_T, R_X1_UP - PARAPET_T, R_Y1 - PARAPET_T,
                            rfl=max(R_R_FL - PARAPET_T, 50.0), rfr=R_R_FR_UP - PARAPET_T),
                  R_H - PARAPET_H, R_H + 100.0)
glz_open_R = box(R_X0 - 1.0, GL_Y0, GL_Z0 - 300.0, R_X0 + GL_REVEAL, 0.0, GL_Z1)
# R does not overlap L: remove the part of R that lies inside L's footprint (Y >= 0, X <= L_X1)
R_in_L = box(L_X0 - 10.0, 0.0, -10.0, L_X1, L_Y1 + 10.0, R_H + 10.0)

# ribbon window void: front face strip from RB_X0 wrapping round the big corner (to the side face)
cxr, cyr = R_X1_UP - R_R_FR_UP, R_Y0 + R_R_FR_UP
outer = [(RB_X0, R_Y0 - 100.0)] + arc_pts(cxr, cyr, R_R_FR_UP + 100.0, 270, 360, 12)
inner = arc_pts(cxr, cyr, R_R_FR_UP - RB_REVEAL, 360, 270, 12) + [(RB_X0, R_Y0 + RB_REVEAL)]
ribbon_void = prism(outer + inner, RB_Z0, RB_Z1)
R = diff(R, [R_in_L, R_roofcut, glz_open_R, ribbon_void])
add(R, "M_Concrete")

# ---------------------------------------------------------------- recess / side glazing
gx = R_X0 + GL_REVEAL - 20.0
add(box(gx, GL_Y0, GL_Z0, gx + 20.0, GL_Y1, GL_Z1), "M_Glass")
# timber mullions (4 bays, ~1.02 m) and floor band, in the glass plane
n_bay = 4
for k in range(n_bay + 1):
    y = GL_Y0 + (GL_Y1 - GL_Y0) * k / float(n_bay)
    add(box(R_X0 + 20.0, y - 40.0, GL_Z0, gx, y + 40.0, GL_Z1), "M_Wood")
add(box(R_X0, GL_Y0, BAND_Z0, gx, GL_Y1, BAND_Z1), "M_Wood")      # inter-floor timber band
add(box(R_X0, GL_Y0, GL_Z1 - 80.0, gx, GL_Y1, GL_Z1), "M_Wood")    # head frame

# slit window glass (fluted glass, recessed)
add(box(SL_REVEAL - 20.0, SL_Y0, SL_Z0, SL_REVEAL, SL_Y1, SL_Z1), "M_Glass")

# ribbon window glass (follows the rounded corner), set back 150 from the face
gr = R_R_FR_UP - 150.0
g_out = [(RB_X0, R_Y0 + 150.0)] + arc_pts(cxr, cyr, gr, 270, 360, 12)
g_in = arc_pts(cxr, cyr, gr - 20.0, 360, 270, 12) + [(RB_X0, R_Y0 + 170.0)]
add(prism(g_out + g_in, RB_Z0, RB_Z1), "M_Glass")

# ---------------------------------------------------------------- carport
add(box(CP_X0, CP_Y0, CP_Z0, CP_X1, CP_Y1, CP_Z1), "M_Concrete")             # thin canopy slab
add(box(R_X1_GF, CP_Y1 - 200.0, 0.0, CP_X1 - 300.0, CP_Y1, CP_Z0), "M_Concrete")  # back wall
add(box(CP_X1 - 500.0, 0.0, 0.0, CP_X1 - 300.0, CP_Y1, CP_Z0), "M_Concrete")      # side wall (supports slab end)
add(box(CP_X1 - 550.0, -3400.0, 0.0, CP_X1 - 300.0, -2200.0, 1900.0), "M_Concrete")  # low wing wall / pier at front

# ---------------------------------------------------------------- site: paving, pool, road
pool_pts = [(POOL_X0, POOL_Y0), (R_X0, POOL_Y0), (R_X0, REC_Y1), (REC_X0, REC_Y1),
            (REC_X0, 0.0), (POOL_X0, 0.0)]
pave = prism(rrect_pts(PAVE_X0, PAVE_Y0, PAVE_X1, PAVE_Y1, rfl=PAVE_CORNER_R), -GROUND_T, 0.0)
pool_cut = prism(pool_pts, -GROUND_T - 50.0, 50.0)
pave = diff(pave, pool_cut)
add(pave, "M_Paving")
# pool basin floor (concrete) and water surface (thin solid)
add(prism(pool_pts, -GROUND_T - 300.0, -GROUND_T), "M_Concrete")
add(prism(pool_pts, WATER_Z - 20.0, WATER_Z), "M_Water")

# road wrapping the corner (front and left), 150 below paving top
rc = PAVE_CORNER_R
road_pts = [(PAVE_X0 - ROAD_W, PAVE_Y0 - ROAD_W), (PAVE_X1, PAVE_Y0 - ROAD_W), (PAVE_X1, PAVE_Y0),
            (PAVE_X0 + rc, PAVE_Y0)]
road_pts += arc_pts(PAVE_X0 + rc, PAVE_Y0 + rc, rc, 270, 180, 8)[1:]
road_pts += [(PAVE_X0, PAVE_Y1), (PAVE_X0 - ROAD_W, PAVE_Y1)]
add(prism(road_pts, -2.0 * GROUND_T, -GROUND_T), "M_Asphalt")

d.Views.Redraw()
result = 'ok'
