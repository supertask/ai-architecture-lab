# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "matplotlib", "shapely>=2"]
# ///
# -*- coding: utf-8 -*-
"""Step 2 — check a layout against the room and the design rules; draw a top-down PNG.

usage:
  uv run check_layout.py my_layout.json            -> PASS / numbered violations, my_layout.png, my_layout.check.json
  uv run check_layout.py --current                 -> checks the arrangement read by read_room.py (current.png)
  uv run check_layout.py --sheet out.png a.json b.json c.json d.json [--title "..."]   -> 2x2 sheet
  options: --room room.json  --png out.png  --paths (draw the reachable floor: dark green = 0.8 m main path, light = 0.6 m)

Layout JSON (only pieces you move need to be listed; the others stay where room.json has them):
  {"request": "...", "title": "...", "concept": "...",
   "pieces": {"sofa": [x, y, facing_deg], ...},
   "exceptions": [{"rule": "sofa_faces_tv", "piece": "sofa", "reason": "..."}]}
"""
import hashlib, json, math, os, sys
from collections import deque
import numpy as np
import shapely
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from matplotlib import font_manager

KIT = os.path.dirname(os.path.abspath(__file__))
for f in ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Noto Sans CJK JP', 'Hiragino Sans', 'IPAexGothic']:
    try:
        font_manager.findfont(f, fallback_to_default=False); plt.rcParams['font.family'] = f; break
    except Exception:
        pass

SEATS = ('sofa', 'lounge_chair', 'pouf', 'stool', 'bench')
SOFT = {  # rule id -> description (soft rules may be waived with an "exceptions" entry + reason)
    'sofa_faces_tv': 'sofa faces the TV within ±{sofa_faces_tv_deg}°',
    'sofa_tv_distance': 'sofa–TV distance {sofa_tv_m[0]}–{sofa_tv_m[1]} m',
    'rug_centred': 'rug centred on the coffee table (≤0.10 m)',
    'rug_under_seats': 'front legs of sofa/lounge chairs (within 2 m of the coffee table) stand on the rug',
    'rug_not_under_tv_unit': 'rug does not run under the TV unit',
    'lounge_to_centre': 'lounge chairs near the coffee table turn to the conversation centre (±{lounge_to_centre_deg}°)',
    'wall_aligned': 'furniture parallel to the walls (0/90/180/270°)',
    'plant_place': 'plants in a corner or beside a piece of furniture',
    'side_table_by_seat': 'side tables within 0.45 m of a seat',
    'lamp_by_seat': 'floor lamp within 0.6 m of a seat',
    'shelf_on_wall': 'shelf back against a wall',
    'chair_at_table': 'dining chairs tucked at the dining table',
}
HARD = {
    'unknown_piece': 'piece id exists in room.json',
    'inside_room': 'inside the room outline',
    'keep_out': 'not in stairs / door clear zones / kitchen counter + aisle',
    'overlap': 'no two pieces overlap',
    'tv_on_unit': 'TV stands on the TV unit, same facing',
    'tv_on_solid_wall': 'TV unit back on a wall with no window/door behind the TV height',
    'dining_chairs': 'dining chairs face the table, evenly spaced, 0.6 m pull-out room',
    'dining_near_kitchen': 'dining table within {dining_to_kitchen_m} m of the kitchen counter',
    'main_path': 'main path ≥ {main_path_m} m: entry → kitchen, doors, other entries, keep-out zones marked reach (stair landing)',
    'secondary_path': 'secondary path ≥ {secondary_path_m} m to every seat, chair and shelf',
}
JA = {'sofa': 'ソファ', 'lounge_chair': 'ラウンジ', 'coffee_table': '座卓', 'side_table': 'サイド', 'rug': '', 'pouf': 'スツール', 'tv_unit': 'TV台',
      'tv': '', 'shelf': '棚', 'dining_table': 'ダイニング', 'dining_chair': '椅子', 'bench': 'ベンチ', 'plant': '植物', 'floor_lamp': '灯',
      'stool': 'スツール', 'other': '?'}
COL = {'sofa': '#8d7b68', 'lounge_chair': '#6f8f7a', 'coffee_table': '#b08a5a', 'side_table': '#c2a37a', 'rug': '#eadfce', 'pouf': '#a7928a',
       'tv_unit': '#555555', 'tv': '#111111', 'shelf': '#a07850', 'dining_table': '#c49a6c', 'dining_chair': '#b9946a', 'bench': '#a07850',
       'plant': '#3f8f4f', 'floor_lamp': '#d9b44a', 'stool': '#a7928a', 'other': '#bbbbbb'}


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def dirv(deg):
    a = math.radians(deg); return math.cos(a), math.sin(a)


def rect(c, facing, w, d):
    fx, fy = dirv(facing); ux, uy = fy, -fx
    return Polygon([(c[0] + sx * ux * w / 2 + sy * fx * d / 2, c[1] + sx * uy * w / 2 + sy * fy * d / 2)
                    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def bearing(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


class Ctx:
    def __init__(self, room, layout):
        self.R = room; self.L = layout or {}
        self.rules = room.get('rules', {})
        self.room = Polygon(room['room']['polygon'])
        self.ext = self.room.exterior
        self.by_id = {f['id']: f for f in room['furniture']}
        self.P = {}
        self.unknown = [k for k in (self.L.get('pieces') or {}) if k not in self.by_id]
        for f in room['furniture']:
            v = (self.L.get('pieces') or {}).get(f['id'])
            c, fa = (v[:2], v[2]) if v else (f['center'], f['facing'])
            self.P[f['id']] = {'id': f['id'], 'kind': f['kind'], 'c': (float(c[0]), float(c[1])), 'f': float(fa), 'w': f['size'][0], 'd': f['size'][1],
                               'h': f['size'][2], 'elev': f.get('elev_m', 0), 'orig': f['center'], 'orig_f': f['facing']}
            self.P[f['id']]['poly'] = rect(self.P[f['id']]['c'], fa, f['size'][0], f['size'][1])
        self.waive = {}
        for e in self.L.get('exceptions') or []:
            self.waive.setdefault(e.get('rule'), set()).add(e.get('piece', '*'))
        self.viol = []; self.waived = []; self.metrics = {}

    def of(self, *kinds):
        return [p for p in self.P.values() if p['kind'] in kinds]

    def add(self, rule, piece, msg, hint=''):
        if rule in SOFT and (piece in self.waive.get(rule, ()) or '*' in self.waive.get(rule, ())):
            self.waived.append((rule, piece, msg)); return
        self.viol.append((rule, piece, msg, hint))


def check(room, layout):
    X = Ctx(room, layout); r = X.rules
    for k in X.unknown:
        X.add('unknown_piece', k, f'"{k}" is not in room.json', 'use the ids printed by read_room.py')
    for e in (layout or {}).get('exceptions') or []:
        if e.get('rule') not in SOFT:
            X.add(e.get('rule', '?'), e.get('piece', '*'), f"rule '{e.get('rule')}' cannot be waived (only {sorted(SOFT)})", 'fix the layout instead')
        elif not e.get('reason'):
            X.add(e['rule'], e.get('piece', '*'), 'exception without a reason', 'add "reason"')
    keep_hard = [Polygon(k['polygon']) for k in room['keep_out']] + [Polygon(f['polygon']) for f in room['fixtures']]
    keep_names = [k['name'] for k in room['keep_out']] + [f['name'] for f in room['fixtures']]
    soft_zones = [(Polygon(o['clear_zone']), 'door clear zone') for o in room['openings'] if o.get('clear_zone')] + \
                 [(Polygon(f['aisle']), f['name'] + ' aisle') for f in room['fixtures'] if f.get('aisle')]
    inner = X.room.buffer(0.005)
    for p in X.P.values():
        q = p['poly']
        if not inner.contains(q):
            out = q.difference(inner).area
            X.add('inside_room', p['id'], f"{p['id']} sticks out of the room ({out:.3f} m²)", 'move it inward')
        for z, nm in zip(keep_hard, keep_names):
            if q.intersection(z).area > 4e-4:
                X.add('keep_out', p['id'], f"{p['id']} is in {nm}", 'move it out of that zone')
        if p['kind'] != 'rug':
            for z, nm in soft_zones:
                if q.intersection(z).area > 4e-4:
                    X.add('keep_out', p['id'], f"{p['id']} blocks the {nm}", 'keep that strip clear')
        if p['kind'] not in ('plant', 'floor_lamp', 'stool', 'pouf') and angdiff(p['f'] % 90, 0) > 1 and angdiff(p['f'] % 90, 90) > 1:
            X.add('wall_aligned', p['id'], f"{p['id']} turned {p['f']:.0f}°", 'use 0/90/180/-90 or add an exception with a reason')
    # overlaps
    solid = [p for p in X.P.values() if p['kind'] != 'rug']
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            ks = {a['kind'], b['kind']}
            if ks in ({'tv', 'tv_unit'}, {'dining_chair', 'dining_table'}, {'bench', 'dining_table'}):
                continue
            ov = a['poly'].intersection(b['poly']).area
            if ov > 4e-4:
                X.add('overlap', a['id'], f"{a['id']} overlaps {b['id']} ({ov:.2f} m²)", 'separate them')
    # TV
    tv = (X.of('tv') or [None])[0]; unit = (X.of('tv_unit') or [None])[0]
    if tv and unit:
        if not unit['poly'].buffer(0.05).contains(Point(tv['c'])) or angdiff(tv['f'], unit['f']) > 10:
            X.add('tv_on_unit', 'tv', 'TV is not on the TV unit (centre inside, same facing)', f"put tv at the unit centre {unit['c']} facing {unit['f']:.0f}")
    if unit:
        fx, fy = dirv(unit['f']); ux, uy = fy, -fx
        bp = (unit['c'][0] - fx * unit['d'] / 2, unit['c'][1] - fy * unit['d'] / 2)
        if X.ext.distance(Point(bp)) > 0.1 or not X.room.contains(Point(unit['c'][0] + fx * 0.5, unit['c'][1] + fy * 0.5)):
            X.add('tv_on_solid_wall', 'tvunit', 'TV unit back is not against a wall (or faces the wall)', 'back on a wall, facing into the room')
        else:
            back = LineString([(bp[0] - ux * unit['w'] / 2, bp[1] - uy * unit['w'] / 2), (bp[0] + ux * unit['w'] / 2, bp[1] + uy * unit['w'] / 2)])
            top = (tv['elev'] + tv['h']) if tv else unit['h'] + 0.6
            for o in room['openings']:
                if not o.get('span'): continue
                if back.distance(LineString(o['span'])) < 0.15 and o['sill_m'] < top + r.get('tv_window_margin_m', 0.3):
                    X.add('tv_on_solid_wall', 'tvunit', f"{o['type']} (sill {o['sill_m']} m) behind the TV", 'choose a wall part without low openings')
                    break
    sofas = X.of('sofa')
    for s in sofas:
        if tv:
            dev = angdiff(bearing(s['c'], tv['c']), s['f']); dist = math.dist(s['c'], tv['c'])
            X.metrics.setdefault('sofa_tv', []).append({'sofa': s['id'], 'deg': round(dev, 1), 'm': round(dist, 2)})
            if dev > r.get('sofa_faces_tv_deg', 15):
                X.add('sofa_faces_tv', s['id'], f"{s['id']} is {dev:.0f}° off the TV", f"turn to {bearing(s['c'], tv['c']):.0f}° or move the TV")
            lo, hi = r.get('sofa_tv_m', [2.0, 3.6])
            if not lo <= dist <= hi:
                X.add('sofa_tv_distance', s['id'], f"sofa–TV {dist:.2f} m (want {lo}–{hi})", 'move sofa or TV')
    # rug / coffee table / lounges
    rug = (X.of('rug') or [None])[0]; cof = (X.of('coffee_table') or [None])[0]
    if rug and cof:
        dd = math.dist(rug['c'], cof['c'])
        if dd > 0.10:
            X.add('rug_centred', 'rug', f"rug centre {dd:.2f} m from coffee table", f"rug centre = coffee table centre {cof['c']}")
        for s in X.of('sofa', 'lounge_chair'):
            if math.dist(s['c'], cof['c']) < 2.0:
                fx, fy = dirv(s['f'])
                leg = Point(s['c'][0] + fx * (s['d'] / 2 - 0.12), s['c'][1] + fy * (s['d'] / 2 - 0.12))
                if not rug['poly'].buffer(0.01).contains(leg):
                    X.add('rug_under_seats', s['id'], f"{s['id']} front legs off the rug", 'move seat 0.1–0.3 m onto the rug or move the rug')
        if unit and rug['poly'].intersection(unit['poly']).area > 4e-4:
            X.add('rug_not_under_tv_unit', 'rug', 'rug runs under the TV unit', 'shift rug away from the TV wall')
        for s in X.of('lounge_chair'):
            if math.dist(s['c'], cof['c']) < 2.2:
                ctr = ((sofas[0]['c'][0] + cof['c'][0]) / 2, (sofas[0]['c'][1] + cof['c'][1]) / 2) if sofas and math.dist(sofas[0]['c'], cof['c']) < 2.0 else cof['c']
                dv = angdiff(bearing(s['c'], ctr), s['f'])
                if dv > r.get('lounge_to_centre_deg', 25):
                    X.add('lounge_to_centre', s['id'], f"{s['id']} {dv:.0f}° off the conversation centre", f"turn to {bearing(s['c'], ctr):.0f}°")
    # dining
    tab = (X.of('dining_table') or [None])[0]
    kitchen = [Polygon(f['polygon']) for f in room['fixtures'] if 'kitchen' in f['kind']]
    if tab:
        ax_ = math.radians(tab['f'] - 90); axv = (math.cos(ax_), math.sin(ax_))  # long axis (width direction)
        sides = {}
        others = [p for p in solid if p['kind'] not in ('dining_chair', 'dining_table', 'bench', 'tv')]
        for ch in X.of('dining_chair'):
            gap = ch['poly'].distance(tab['poly'])
            if gap > 0.05:
                X.add('chair_at_table', ch['id'], f"{ch['id']} not at the table ({gap:.2f} m)", 'tuck it to the table edge'); continue
            if angdiff(bearing(ch['c'], tab['c']), ch['f']) > 45:
                X.add('dining_chairs', ch['id'], f"{ch['id']} does not face the table", f"turn to {bearing(ch['c'], tab['c']):.0f}°")
            fx, fy = dirv(ch['f']); po = r.get('chair_pull_out_m', 0.6) - 0.04
            B = rect((ch['c'][0] - fx * po, ch['c'][1] - fy * po), ch['f'], ch['w'], ch['d'])
            hit = [o['id'] for o in others if B.intersection(o['poly']).area > 4e-4] + \
                  [nm for z, nm in zip(keep_hard, keep_names) if B.intersection(z).area > 4e-4]
            if not X.room.buffer(0.005).contains(B): hit.append('wall')
            if hit:
                X.add('dining_chairs', ch['id'], f"{ch['id']} cannot be pulled out 0.6 m ({', '.join(hit)})", 'give 0.6 m behind every chair')
            u = (ch['c'][0] - tab['c'][0]) * axv[0] + (ch['c'][1] - tab['c'][1]) * axv[1]
            v = -(ch['c'][0] - tab['c'][0]) * axv[1] + (ch['c'][1] - tab['c'][1]) * axv[0]
            if abs(u) < tab['w'] / 2 - 0.05:
                sides.setdefault('a' if v > 0 else 'b', []).append(u)
        for sd, us in sides.items():
            if (len(us) == 1 and abs(us[0]) > 0.05) or (len(us) == 2 and (abs(us[0] + us[1]) > 0.05)) or len(us) > 2 and abs(sum(us)) > 0.05:
                X.add('dining_chairs', 'dchair', f"chairs on one long side not evenly spaced (offsets {[round(x, 2) for x in us]})", 'mirror them about the table centre')
        if kitchen:
            dk = min(tab['poly'].distance(k) for k in kitchen)
            X.metrics['dining_to_kitchen_m'] = round(dk, 2)
            if dk > r.get('dining_to_kitchen_m', 2.5):
                X.add('dining_near_kitchen', tab['id'], f"dining table {dk:.2f} m from the kitchen counter", 'bring it closer')
    # plants / side tables / lamp / shelf
    nearby = [p for p in X.P.values() if p['kind'] in ('sofa', 'lounge_chair', 'side_table', 'shelf', 'tv_unit', 'dining_table', 'bench', 'coffee_table')]
    for p in X.of('plant'):
        c = p['c']; out = [not X.room.contains(Point(c[0] + dx, c[1] + dy)) for dx, dy in ((0.45, 0), (-0.45, 0), (0, 0.45), (0, -0.45))]
        corner = (out[0] or out[1]) and (out[2] or out[3])
        beside = any(p['poly'].distance(q['poly']) < 0.5 for q in nearby)
        if not corner and not beside:
            X.add('plant_place', p['id'], f"{p['id']} is neither in a corner nor beside furniture", 'corner or next to a seat/shelf')
    seats = X.of('sofa', 'lounge_chair')
    for p in X.of('side_table'):
        if seats and min(p['poly'].distance(s['poly']) for s in seats) > 0.45:
            X.add('side_table_by_seat', p['id'], f"{p['id']} is not beside a seat", 'put it next to a sofa/lounge chair')
    for p in X.of('floor_lamp'):
        if seats and min(p['poly'].distance(s['poly']) for s in seats) > 0.6:
            X.add('lamp_by_seat', p['id'], f"{p['id']} is not beside a seat", 'put it by a sofa/lounge chair')
    for p in X.of('shelf'):
        fx, fy = dirv(p['f'])
        if X.ext.distance(Point(p['c'][0] - fx * p['d'] / 2, p['c'][1] - fy * p['d'] / 2)) > 0.1:
            X.add('shelf_on_wall', p['id'], f"{p['id']} back is not on a wall", 'back against a wall, facing the room')
    paths(X, room, solid)
    moves(X)
    return X


def grid(X, obst, rad, res=0.05):
    x0, y0, x1, y1 = X.room.bounds
    xs = np.arange(x0, x1, res) + res / 2; ys = np.arange(y0, y1, res) + res / 2
    GX, GY = np.meshgrid(xs, ys)
    pts = shapely.points(GX.ravel(), GY.ravel())
    inside = shapely.contains_xy(X.room, GX.ravel(), GY.ravel())
    dwall = shapely.distance(X.ext, pts)
    dobs = shapely.distance(obst, pts) if obst is not None and not obst.is_empty else np.full(len(pts), 1e9)
    free = inside & (dwall >= rad) & (dobs >= rad)
    return free.reshape(GX.shape), GX, GY, inside.reshape(GX.shape), np.minimum(dwall, dobs).reshape(GX.shape)


def bfs(free, GX, GY, src):
    d = (GX - src[0]) ** 2 + (GY - src[1]) ** 2
    d = np.where(free, d, np.inf)
    i = np.unravel_index(np.argmin(d), d.shape)
    seen = np.zeros(free.shape, bool)
    if not np.isfinite(d[i]) or d[i] > 0.6 ** 2:
        return seen
    seen[i] = True; q = deque([i]); H, W = free.shape
    while q:
        a, b = q.popleft()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            aa, bb = a + da, b + db
            if 0 <= aa < H and 0 <= bb < W and free[aa, bb] and not seen[aa, bb]:
                seen[aa, bb] = True; q.append((aa, bb))
    return seen


def paths(X, room, solid):
    r = X.rules
    obst = unary_union([p['poly'] for p in solid if p['kind'] != 'tv'] + [Polygon(f['polygon']) for f in room['fixtures']] +
                       [Polygon(k['polygon']) for k in room['keep_out'] if k.get('source') == 'zone'])
    ents = room['entries']
    if not ents:
        X.add('main_path', '*', 'no entry in room.json', 'set entries in config.json'); return
    src = ents[0]['point']
    mfree, GX, GY, inside, clear = grid(X, obst, r.get('main_path_m', 0.8) / 2)
    seen = bfs(mfree, GX, GY, src)
    X._grid = (GX, GY, seen)
    tg = [(f['name'], f['front_point']) for f in room['fixtures'] if f.get('front_point')] + \
         [(f"door {o['lib'] or ''}".strip(), o['approach_point']) for o in room['openings'] if o.get('approach_point')] + \
         [(e['name'], e['point']) for e in ents[1:]] +          [(k['name'], list(Polygon(k['polygon']).centroid.coords)[0]) for k in room['keep_out'] if k.get('reach')]
    for nm, pt in tg:
        if not (seen & (((GX - pt[0]) ** 2 + (GY - pt[1]) ** 2) < 0.35 ** 2)).any():
            X.add('main_path', nm, f"main path ({r.get('main_path_m', 0.8)} m) blocked: {ents[0]['name']} → {nm}", 'open a 0.8 m lane')
    sfree, GX, GY, _, _ = grid(X, obst, r.get('secondary_path_m', 0.6) / 2)
    seen2 = bfs(sfree, GX, GY, src)
    X._grid2 = seen2
    rx, ry = GX[seen2], GY[seen2]
    pts = shapely.points(rx, ry)
    for p in X.P.values():
        if p['kind'] in SEATS + ('dining_chair', 'shelf'):
            tgt = p['poly']
            if p['kind'] == 'dining_chair':
                fx, fy = dirv(p['f']); tgt = rect((p['c'][0] - fx * 0.56, p['c'][1] - fy * 0.56), p['f'], p['w'], p['d'])
            if not len(pts) or shapely.distance(tgt, pts).min() > 0.45:
                X.add('secondary_path', p['id'], f"no {r.get('secondary_path_m', 0.6)} m path to {p['id']}", 'leave a 0.6 m gap to reach it')
    # open floor: largest clear circle (everything except the rug counts as an obstacle)
    m = np.where(inside, clear, 0)
    i = np.unravel_index(np.argmax(m), m.shape)
    X.metrics['open_floor_circle_m'] = round(float(m[i]) * 2, 2)
    X.metrics['open_floor_centre'] = [round(float(GX[i]), 2), round(float(GY[i]), 2)]


def moves(X):
    mv = []
    for p in X.P.values():
        d = math.dist(p['c'], p['orig'])
        if d > 0.05 or angdiff(p['f'], p['orig_f']) > 1:
            mv.append((p['id'], round(d, 2), round(angdiff(p['f'], p['orig_f']))))
    mv.sort(key=lambda x: -x[1])
    X.metrics['moved'] = mv
    X.metrics['moved_n'] = len(mv)
    big = [m for m in mv if m[1] >= X.rules.get('big_move_m', 3.0)]
    X.metrics['moved_3m_plus'] = [m[0] for m in big]
    X.metrics['max_move_m'] = mv[0][1] if mv else 0


def draw(X, ax, title, sub=None):
    R = X.R
    ax.set_facecolor('white')
    ax.add_patch(MPoly(R['room']['polygon'], closed=True, fc='#fbfaf7', ec='#222', lw=3.2, zorder=1))
    for k in R['keep_out']:
        ax.add_patch(MPoly(k['polygon'], closed=True, fc='#eeeeee', ec='#777', hatch='///', lw=0.8, zorder=1.5))
        c = Polygon(k['polygon']).representative_point()
        ax.text(c.x, c.y, k['name'].replace('（', '\n（'), ha='center', va='center', fontsize=6.5, color='#555', zorder=1.6)
    for f in R['fixtures']:
        ax.add_patch(MPoly(f['polygon'], closed=True, fc='#f1f1f1', ec='#555', ls='--', lw=1.1, zorder=1.5))
        c = Polygon(f['polygon']).centroid
        ax.text(c.x, c.y, f['name'], ha='center', va='center', fontsize=7, zorder=1.6)
    for o in R['openings']:
        if not o.get('span'): continue
        (a, b) = o['span']
        if o['type'] == 'window':
            ax.plot([a[0], b[0]], [a[1], b[1]], color='#2a7fcf' if o['sill_m'] < 1.0 else '#8ec5f2', lw=5 if o['sill_m'] < 1.0 else 3.2, solid_capstyle='butt', zorder=2)
        else:
            ax.plot([a[0], b[0]], [a[1], b[1]], color='#e69a1a', lw=5, solid_capstyle='butt', zorder=2)
            if o.get('clear_zone'):
                ax.add_patch(MPoly(o['clear_zone'], closed=True, fill=False, ec='#e69a1a', ls=':', lw=1, zorder=1.5))
    for e in R['entries']:
        ax.annotate('入口', e['point'], xytext=(e['point'][0], e['point'][1] + 0.0), ha='center', va='center', fontsize=7.5, color='#1e5aa8',
                    bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='#1e5aa8', lw=0.6), zorder=8)
    bad = {v[1] for v in X.viol}
    if '--paths' in sys.argv and hasattr(X, '_grid'):
        GX, GY, seen = X._grid
        ax.scatter(GX[X._grid2], GY[X._grid2], s=0.4, c='#9fd89f', zorder=1.8, label='0.6 m')
        ax.scatter(GX[seen], GY[seen], s=0.4, c='#3a9a3a', zorder=1.9, label='0.8 m')
    # ghosts + move arrows
    for p in X.P.values():
        d = math.dist(p['c'], p['orig'])
        if d > 0.3:
            g = rect(p['orig'], p['orig_f'], p['w'], p['d'])
            ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fill=False, ec='#b5b5b5', ls='--', lw=0.6, zorder=2.5))
            if p['kind'] not in ('rug', 'tv') and d > 1.0:
                ax.annotate('', p['c'], p['orig'], arrowprops=dict(arrowstyle='->', color='#9a9a9a', lw=0.7, shrinkA=0, shrinkB=4), zorder=2.6)
    order = sorted(X.P.values(), key=lambda p: (p['kind'] != 'rug', p['kind'] == 'tv'))
    for p in order:
        q = list(p['poly'].exterior.coords)
        ax.add_patch(MPoly(q, closed=True, fc=COL.get(p['kind'], '#bbb'), ec='#d0021b' if p['id'] in bad else '#333',
                           lw=2.0 if p['id'] in bad else 0.7, alpha=0.82 if p['kind'] == 'rug' else 0.95, zorder=3 if p['kind'] == 'rug' else 4))
        if p['kind'] in ('sofa', 'lounge_chair', 'dining_chair', 'tv'):
            fx, fy = dirv(p['f']); s = (p['c'][0] + fx * p['d'] / 2, p['c'][1] + fy * p['d'] / 2)
            ax.annotate('', (s[0] + fx * 0.25, s[1] + fy * 0.25), s, arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.1), zorder=6)
        t = JA.get(p['kind'], '')
        if t:
            ax.text(p['c'][0], p['c'][1], t, ha='center', va='center', fontsize=6 if p['kind'] in ('dining_chair', 'side_table', 'plant', 'floor_lamp', 'pouf', 'stool') else 7.5,
                    color='white' if p['kind'] in ('sofa', 'tv_unit', 'lounge_chair', 'plant') else 'black', zorder=7)
    x0, y0, x1, y1 = R['room']['bbox']
    ax.set_xlim(x0 - 0.4, x1 + 0.4); ax.set_ylim(y0 - 1.05, y1 + 0.55); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(title, fontsize=14, loc='left')
    ok = X.viol == []
    s1 = ('ルール確認 PASS' if ok else f'違反 {len(X.viol)} 件: ' + ' / '.join(v[0] for v in X.viol[:3]))
    met = X.metrics
    s2 = f"動かした家具 {met.get('moved_n', 0)} 点・最大 {met.get('max_move_m', 0)} m・空き床の最大円 直径{met.get('open_floor_circle_m', '?')} m"
    if met.get('sofa_tv'): s2 += f"・ソファ–TV {met['sofa_tv'][0]['m']} m"
    if X.waived: s2 += f"・例外 {len(X.waived)}（{', '.join(sorted({w[0] for w in X.waived}))}）"
    ax.text(x0 - 0.35, y0 - 0.45, s1, fontsize=8.5, color='#1e7d32' if ok else '#c0392b')
    ax.text(x0 - 0.35, y0 - 0.85, s2, fontsize=7.5, color='#333')
    if sub:
        ax.text(x0 - 0.35, y1 + 0.3, sub, fontsize=8, color='#444')
    ax.plot([x1 - 1.0, x1], [y1 + 0.42, y1 + 0.42], color='k', lw=2); ax.text(x1 - 0.5, y1 + 0.36, '1 m', ha='center', va='top', fontsize=7)


def report(X, layout_path=None):
    lines = []
    if not X.viol:
        lines.append('PASS')
    else:
        lines.append(f'FAIL ({len(X.viol)})')
        for i, (rule, piece, msg, hint) in enumerate(X.viol, 1):
            lines.append(f'{i}. [{rule}] {msg}' + (f'  -> {hint}' if hint else ''))
    for w in X.waived:
        lines.append(f'   waived [{w[0]}] {w[2]}')
    m = X.metrics
    lines.append(f"moved {m.get('moved_n')} pieces, max {m.get('max_move_m')} m, >=3 m: {m.get('moved_3m_plus')}")
    lines.append('  ' + ', '.join(f'{a} {b} m' + (f' {c}°' if c else '') for a, b, c in m.get('moved', [])[:12]))
    lines.append(f"open floor: largest clear circle {m.get('open_floor_circle_m')} m at {m.get('open_floor_centre')}"
                 + (f"; sofa-TV {m['sofa_tv']}" if m.get('sofa_tv') else '') + (f"; dining-kitchen {m.get('dining_to_kitchen_m')} m" if 'dining_to_kitchen_m' in m else ''))
    return '\n'.join(lines)


def main():
    room = json.load(open(arg('--room', os.path.join(KIT, 'room.json')), encoding='utf-8'))
    if '--sheet' in sys.argv:
        out = arg('--sheet'); files = [a for a in sys.argv[1:] if a.endswith('.json') and a != arg('--room')]
        fig, axs = plt.subplots(2, 2, figsize=(15, 13.2), dpi=110)
        for ax, fpath in zip(axs.flat, files):
            L = json.load(open(fpath, encoding='utf-8')); X = check(room, L)
            draw(X, ax, L.get('title', os.path.basename(fpath)), '「' + L.get('request', '') + '」')
        for ax in list(axs.flat)[len(files):]:
            ax.axis('off')
        fig.suptitle(arg('--title', 'AIの家具配置（自由文 → Archicadの部屋を読む → ルール確認 → 反映）'), fontsize=17)
        fig.text(0.5, 0.935, '凡例: 濃い青=床からの窓  薄い青=高窓  橙=ドア(点線=開閉の空き)  斜線=階段  点線=キッチン(仮定)  赤矢印=座る向き  灰色の点線=元の位置',
                 ha='center', fontsize=10)
        fig.tight_layout(rect=(0, 0, 1, 0.925)); fig.savefig(out); plt.close(fig)
        print('sheet ->', out); return
    if '--current' in sys.argv:
        L = {'title': '現在の配置', 'pieces': {}}; path = os.path.join(KIT, 'current.json')
    else:
        path = [a for a in sys.argv[1:] if a.endswith('.json') and a != arg('--room')][0]
        L = json.load(open(path, encoding='utf-8'))
    X = check(room, L)
    txt = report(X)
    print(txt)
    stem = os.path.splitext(path)[0]
    png = arg('--png', stem + '.png')
    fig, ax = plt.subplots(figsize=(9, 8.2), dpi=120)
    draw(X, ax, L.get('title', os.path.basename(path)), ('「' + L['request'] + '」') if L.get('request') else None)
    fig.tight_layout(); fig.savefig(png); plt.close(fig)
    sha = hashlib.sha256(json.dumps(L.get('pieces', {}), sort_keys=True).encode()).hexdigest()
    if '--current' not in sys.argv:
        json.dump({'status': 'PASS' if not X.viol else 'FAIL', 'violations': [list(v) for v in X.viol], 'waived': X.waived,
                   'metrics': X.metrics, 'pieces_sha256': sha, 'room_read_at': room.get('read_at')},
                  open(stem + '.check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('png ->', png)


if __name__ == '__main__':
    main()
