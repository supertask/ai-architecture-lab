# -*- coding: utf-8 -*-
# B_image_plus_drawing : massing model from exterior image + v14 drawing sheet
# RhinoCommon script (IronPython / CPython). Units: mm.
# Coordinates: Z up. Street on -Y side (front faces -Y). X to the right seen from street.
# Origin: x=0 = left edge of the left box (plan grid line), y=0 = front line of the
# building (1F plan front edge, 1 m behind the road line). Back wall at y=11100.
import math
import System
import System.Drawing
import Rhino
import Rhino.Geometry as G

d = Rhino.RhinoDoc.ActiveDoc
TOL = max(d.ModelAbsoluteTolerance, 0.01)
ARC_SEGS = 16  # polyline segments per 90 deg of rounded corner

try:
    if d.ModelUnitSystem != Rhino.UnitSystem.Millimeters:
        d.ModelUnitSystem = Rhino.UnitSystem.Millimeters
except Exception:
    pass

# ---------------------------------------------------------------- clear doc
for _id in [o.Id for o in d.Objects]:
    d.Objects.Delete(_id, True)

# ---------------------------------------------------------------- layers
def get_layer(name, rgb):
    idx = d.Layers.FindByFullPath(name, -1)
    if idx < 0:
        lay = Rhino.DocObjects.Layer()
        lay.Name = name
        lay.Color = System.Drawing.Color.FromArgb(rgb[0], rgb[1], rgb[2])
        idx = d.Layers.Add(lay)
    return idx

LAY = {
    'M_Concrete': get_layer('M_Concrete', (190, 188, 182)),
    'M_Glass': get_layer('M_Glass', (90, 170, 230)),
    'M_Wood': get_layer('M_Wood', (190, 130, 70)),
    'M_Water': get_layer('M_Water', (40, 90, 120)),
    'M_Paving': get_layer('M_Paving', (215, 212, 205)),
    'M_Asphalt': get_layer('M_Asphalt', (60, 60, 62)),
}

def add(breps, layer):
    if breps is None:
        return
    if isinstance(breps, G.Brep):
        breps = [breps]
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = LAY[layer]
    for b in breps:
        if b is not None:
            d.Objects.AddBrep(b, a)

# ---------------------------------------------------------------- geometry helpers
def _unit(vx, vy):
    l = math.sqrt(vx * vx + vy * vy)
    return vx / l, vy / l

def fillet_pts(pts, radii):
    """Closed orthogonal polygon -> point list with arc points at corners (radius mm, 0 = sharp)."""
    n = len(pts)
    out = []
    for i in range(n):
        px, py = pts[i]
        ax, ay = pts[i - 1]
        bx, by = pts[(i + 1) % n]
        r = radii[i]
        if r <= 0:
            out.append((px, py))
            continue
        ux, uy = _unit(ax - px, ay - py)
        vx, vy = _unit(bx - px, by - py)
        cx, cy = px + (ux + vx) * r, py + (uy + vy) * r      # 90 deg corners
        a0 = math.atan2(py + uy * r - cy, px + ux * r - cx)
        a1 = math.atan2(py + vy * r - cy, px + vx * r - cx)
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(ARC_SEGS + 1):
            t = a0 + da * k / float(ARC_SEGS)
            out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return out

def poly_curve(pts):
    pl = G.Polyline()
    for x, y in pts:
        pl.Add(G.Point3d(x, y, 0))
    pl.Add(G.Point3d(pts[0][0], pts[0][1], 0))
    return G.PolylineCurve(pl)

def extrude(pts, z0, z1):
    c = poly_curve(pts)
    c.Translate(G.Vector3d(0, 0, z0))
    srf = G.Surface.CreateExtrusion(c, G.Vector3d(0, 0, z1 - z0))
    b = srf.ToBrep()
    try:
        b.Faces.SplitKinkyFaces(Rhino.RhinoMath.DefaultAngleTolerance, True)
    except Exception:
        pass
    b = b.CapPlanarHoles(TOL)
    if b is not None and b.SolidOrientation == G.BrepSolidOrientation.Inward:
        b.Flip()
    return b

def rpoly(pts, radii, z0, z1):
    return extrude(fillet_pts(pts, radii), z0, z1)

def box(x0, y0, z0, x1, y1, z1):
    return G.Box(G.BoundingBox(G.Point3d(min(x0, x1), min(y0, y1), min(z0, z1)),
                               G.Point3d(max(x0, x1), max(y0, y1), max(z0, z1)))).ToBrep()

def diff(a, cutters):
    res = [a]
    for c in cutters:
        nxt = []
        for r in res:
            out = G.Brep.CreateBooleanDifference(r, c, TOL)
            if out is None or len(out) == 0:
                nxt.append(r)          # no intersection / failure -> keep
            else:
                nxt.extend(list(out))
        res = nxt
    return res

# ---------------------------------------------------------------- dimensions (mm)
DEPTH = 11100          # building depth (1F plan)
X_LEG = 1000           # left wall leg thickness (recess left side)
X_NOTCH = 6000         # left face of right box / notch
X_GLASS = 7000         # recess glass line
Y_NOTCH = 1300         # notch depth (front 1.3 m)
Y_ROOF = 2800          # front edge of left box / recess roof (green line), end of leg
Y_RECESS = 6800        # recess back wall
X_LEFTBOX = 12600      # left box right end / garage left
X_RIGHTBOX = 15300     # right (2F) box right end
X_TOTAL = 18000        # 1F-only part right end
X_GAR_IN = 17300       # garage interior right (0.7 m side wall)
Y_GAR_IN = 10400       # garage interior back (0.7 m back wall)
H_LEFT = 7500
H_RIGHT = 6800
H_RECESS = 5800
H_1F_ONLY = 3300
H_GARAGE = 2700
R_BACKLEFT = 2000
R_RIGHTBOX = 1500      # front-right & back-right of right box, also 1F corner at garage
R_NOTCH = 500
R_1F_BACKRIGHT = 1200
R_GAR_IN = 500
RIB_Z0, RIB_Z1, RIB_X0 = 4700, 5900, 7100
SLIT_Y0, SLIT_Y1, SLIT_Z0, SLIT_Z1 = 3200, 4500, 300, 5800
BACK1_X0, BACK1_X1, BACK1_Z0, BACK1_Z1 = 2400, 6800, 0, 2400      # height guessed
BACK2_X0, BACK2_X1 = 8000, 12000
REVEAL = 150
GLASS_T = 20
FL_2F = 3200           # guessed 2F floor level (wood slab-edge band)

# ---------------------------------------------------------------- recess voids
# Recess = x 1.0-7.0. In front of the green line (y<2.8, x 1-6) nothing is built (open to sky),
# so only the roofed part needs cutting: x 1-7, y 1.3-6.8, z <5.8 (cutter overshoots to avoid coplanar faces).
# Behind the notch (x 6-7, y 1.3-2.8) the right box covers it at 5.8-6.8 (green line step).
V_roofed = box(X_LEG, Y_NOTCH, -500, X_GLASS, Y_RECESS, H_RECESS)
RECESS = [V_roofed]

# ---------------------------------------------------------------- window cutters / glass
def ribbon_path(off):
    """front ribbon path offset 'off' inward from the facade (y=0 face, arc r1500 at x=15300)."""
    cx, cy, r = X_RIGHTBOX - R_RIGHTBOX, R_RIGHTBOX, R_RIGHTBOX - off
    pts = [(RIB_X0, off)]
    for k in range(ARC_SEGS + 1):
        t = -math.pi / 2 + (math.pi / 2) * k / float(ARC_SEGS)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts

def band_between(p_out, p_in):
    return p_out + list(reversed(p_in))

ribbon_cut = extrude(band_between(ribbon_path(-200), ribbon_path(REVEAL)), RIB_Z0, RIB_Z1)
slit_cut = box(-200, SLIT_Y0, SLIT_Z0, 250, SLIT_Y1, SLIT_Z1)
back1_cut = box(BACK1_X0, DEPTH - REVEAL, BACK1_Z0 - 10, BACK1_X1, DEPTH + 200, BACK1_Z1)
back2_cut = box(BACK2_X0, DEPTH - REVEAL, RIB_Z0, BACK2_X1, DEPTH + 200, RIB_Z1)

# ---------------------------------------------------------------- concrete masses
# Left box (yellowish in front elevation): x 0-12.6, y 2.8-11.1, h 7.5, back-left corner r2.0
left_box = rpoly([(0, Y_ROOF), (X_LEFTBOX, Y_ROOF), (X_LEFTBOX, DEPTH), (0, DEPTH)],
                 [0, 0, 0, R_BACKLEFT], 0, H_LEFT)
add(diff(left_box, RECESS + [slit_cut, back1_cut, back2_cut]), 'M_Concrete')

# Right box, 1F part in front of the left box (garage corner rounded r1.5)
r1 = rpoly([(X_NOTCH, 0), (X_LEFTBOX, 0), (X_LEFTBOX, Y_ROOF), (X_NOTCH, Y_ROOF)],
           [R_NOTCH, R_RIGHTBOX, 0, 0], 0, H_GARAGE)
add(diff(r1, RECESS), 'M_Concrete')

# Right box upper (h 6.8): over the garage up to x 15.3, rounded front-right / back-right r1.5
R2_PTS = [(X_NOTCH, 0), (X_RIGHTBOX, 0), (X_RIGHTBOX, DEPTH), (X_LEFTBOX, DEPTH),
          (X_LEFTBOX, Y_ROOF), (X_NOTCH, Y_ROOF)]
R2_RAD = [R_NOTCH, R_RIGHTBOX, R_RIGHTBOX, 0, 0, 0]
r2 = rpoly(R2_PTS, R2_RAD, H_GARAGE, H_RIGHT)
add(diff(r2, RECESS + [ribbon_cut]), 'M_Concrete')

# 1F-only part + garage walls (h 3.3), garage interior 4.7 x 10.4, opening h 2.7, open to the road
G_PTS = [(X_LEFTBOX, 0), (X_TOTAL, 0), (X_TOTAL, DEPTH), (X_LEFTBOX, DEPTH)]
G_RAD = [0, 0, R_1F_BACKRIGHT, 0]
g_walls = rpoly(G_PTS, G_RAD, 0, H_GARAGE)
garage_void = rpoly([(X_LEFTBOX - 10, -1000), (X_GAR_IN, -1000), (X_GAR_IN, Y_GAR_IN), (X_LEFTBOX - 10, Y_GAR_IN)],
                    [0, 0, R_GAR_IN, 0], -100, H_GARAGE + 100)
add(diff(g_walls, [garage_void]), 'M_Concrete')
# 1F roof slab 2.7-3.3 only outside the right box footprint (incl. outside its r1.5 corners)
g_slab = rpoly(G_PTS, G_RAD, H_GARAGE, H_1F_ONLY)
r2_clear = rpoly(R2_PTS, R2_RAD, H_GARAGE - 100, H_1F_ONLY + 100)
add(diff(g_slab, [r2_clear]), 'M_Concrete')

# ---------------------------------------------------------------- glazing
# recess glass wall on x=7.0 (right face of recess), y 1.3-6.8, z 0-5.8 (double height)
add(box(X_GLASS - GLASS_T, Y_NOTCH, 0, X_GLASS, Y_RECESS, H_RECESS), 'M_Glass')
# timber mullions (4 bays, from image) + slab-edge band at 2F floor
mul = []
n_bays = 4
for k in range(n_bays + 1):
    yc = Y_NOTCH + (Y_RECESS - Y_NOTCH) * k / float(n_bays)
    y0 = max(Y_NOTCH, yc - 40)
    y1 = min(Y_RECESS, yc + 40)
    mul.append(box(X_GLASS - GLASS_T - 150, y0, 0, X_GLASS - GLASS_T, y1, H_RECESS))
mul.append(box(X_GLASS - GLASS_T - 150, Y_NOTCH, FL_2F - 300, X_GLASS - GLASS_T, Y_RECESS, FL_2F))
add(mul, 'M_Wood')

# front ribbon window (2F, 4.7-5.9 m), panes split at x 9.4 / 11.7 / 13.8, wraps the r1.5 corner
gl0, gl1 = REVEAL - GLASS_T, REVEAL
ribbon = []
for xa, xb in [(RIB_X0, 9385), (9415, 11685), (11715, X_RIGHTBOX - R_RIGHTBOX)]:
    ribbon.append(box(xa, gl0, RIB_Z0, xb, gl1, RIB_Z1))
arc_out = ribbon_path(gl0)[1:]
arc_in = ribbon_path(gl1)[1:]
ribbon.append(extrude(band_between(arc_out, arc_in), RIB_Z0, RIB_Z1))
add(ribbon, 'M_Glass')

# slit window on the left side face (x=0), deep reveal 250
add(box(250 - GLASS_T, SLIT_Y0, SLIT_Z0, 250, SLIT_Y1, SLIT_Z1), 'M_Glass')
# back windows (y=11.1 face)
add(box(BACK1_X0, DEPTH - REVEAL, BACK1_Z0, BACK1_X1, DEPTH - REVEAL + GLASS_T, BACK1_Z1), 'M_Glass')
add(box(BACK2_X0, DEPTH - REVEAL, RIB_Z0, BACK2_X1, DEPTH - REVEAL + GLASS_T, RIB_Z1), 'M_Glass')

# ---------------------------------------------------------------- pool (image only)
POOL = [(X_LEG, -700), (X_NOTCH, -700), (X_NOTCH, Y_NOTCH), (X_GLASS - 300, Y_NOTCH),
        (X_GLASS - 300, 5800), (X_LEG, 5800)]
pool_fp = extrude(POOL, -1000, 100)
add(extrude(POOL, -100 - GLASS_T, -100), 'M_Water')            # water surface 100 below grade
add(extrude(POOL, -400, -300), 'M_Concrete')                     # basin floor

# ---------------------------------------------------------------- ground / sidewalk / road
SITE = [(-1000, -1000), (40000, -1000), (40000, 30000), (-1000, 30000)]
site = rpoly(SITE, [3000, 0, 0, 0], -300, 0)                     # paving incl. 1 m sidewalk strip
add(diff(site, [pool_fp]), 'M_Paving')
road_full = box(-10000, -10000, -450, 40000, 30000, -150)        # road 150 below sidewalk (curb)
site_cut = rpoly(SITE, [3000, 0, 0, 0], -1000, 100)
add(diff(road_full, [site_cut]), 'M_Asphalt')                    # front road + left road (corner lot)

d.Views.Redraw()
result = 'ok'
