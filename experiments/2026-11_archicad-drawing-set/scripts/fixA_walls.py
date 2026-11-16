"""修正A-1：壁を複合構造に。外壁は室内側を部屋（ゾーン）で判定し、RC が外側に来る向きの複合構造を選ぶ。
規則（11/16 確認）：flipped=True の壁では、複合構造の最初の層が進行方向の右側に来る。"""
import os, sys, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT); import tapir_http as t
P = int(os.environ.get('ARCHICAD_PORT', '19723'))
C = json.load(open(os.path.join(KIT, 'fixA_comps.json'), encoding='utf-8'))
W = json.load(open(os.path.join(KIT, 'walls_before_fixA.json')))
zs = t.call(P, 'GetElementsByType', {'elementType': 'Zone'})['elements']
zd = t.call(P, 'GetDetailsOfElements', {'elements': zs})['detailsOfElements']
zones = []
for d in zd:
    x = d['details']; poly = x.get('polygonOutline') or x.get('polygonCoordinates')
    zones.append((d.get('floorIndex'), [(p['x'], p['y']) for p in poly]))
def inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def inzone(pt, f): return any(inside(pt, p) for fi, p in zones if fi == f)
cent = {}
for f in (0, 1):
    pts = [q for fi, p in zones if fi == f for q in p]
    cent[f] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
mods = []; log = []
for w in W:
    if w['t'] < 0.15:
        mods.append({'elementId': {'guid': w['g']}, 'structureType': 'Composite', 'compositeId': C['架空_間仕切 PB12.5 LGS95 PB12.5']}); continue
    ax, ay, bx, by = w['a']['x'], w['a']['y'], w['b']['x'], w['b']['y']
    L = ((bx - ax) ** 2 + (by - ay) ** 2) ** .5; dx, dy = (bx - ax) / L, (by - ay) / L
    nx, ny = -dy, dx  # 進行方向の左
    m = ((ax + bx) / 2, (ay + by) / 2); f = w['f']
    side = None
    for dist in (0.3, 1.0):
        l = inzone((m[0] + nx * dist, m[1] + ny * dist), f); r = inzone((m[0] - nx * dist, m[1] - ny * dist), f)
        if l != r: side = 'L' if l else 'R'; how = f'zone{dist}'; break
    if side is None:
        c = cent[f]; side = 'L' if (c[0] - m[0]) * nx + (c[1] - m[1]) * ny > 0 else 'R'; how = 'centroid'
    comp = '架空_外壁 RC打放し150 断熱35 PB' if side == 'L' else '架空_外壁(逆) PB 断熱35 RC打放し150'
    mods.append({'elementId': {'guid': w['g']}, 'structureType': 'Composite', 'compositeId': C[comp]})
    log.append((w['g'][:6], f, (ax, ay), (bx, by), side, how))
for l in log: print(*l)
r = t.call(P, 'ModifyWalls', {'wallsWithDetails': mods})
print(sum(1 for x in r['executionResults'] if x.get('success')), '/', len(mods))
