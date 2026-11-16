"""修正A-2：床・屋根を複合構造に、厚い塊の屋根を「屋根の板＋天井＋縁の壁」に分ける。"""
import os, sys, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT); import tapir_http as t
P = int(os.environ.get('ARCHICAD_PORT', '19723'))
C = json.load(open(os.path.join(KIT, 'fixA_comps.json'), encoding='utf-8'))
ROOF, FL2, CEIL, FL1 = (C['架空_屋根 押えコン60 断熱30 防水10 RC200'], C['架空_2階床 フローリング15 置床85 RC200'],
                        C['架空_天井 LGS40 PB9.5'], C['架空_1階床 フローリング15 断熱85 RC土間150 砕石100'])
bm = {a['name']: a['attributeId'] for a in t.call(P, 'GetAttributesByType', {'attributeType': 'BuildingMaterial'})['attributes']}
CONC = bm['コンクリート']
ST = {s['index']: s['level'] for s in t.call(P, 'GetStories', {})['stories']}
def story_of(z): return max(i for i, l in ST.items() if l <= z + 1e-6)
sl = t.call(P, 'GetElementsByType', {'elementType': 'Slab'})['elements']
dd = t.call(P, 'GetDetailsOfElements', {'elements': sl})['detailsOfElements']
bb = t.call(P, 'Get3DBoundingBoxes', {'elements': sl})['boundingBoxes3D']
S = {}
for e, d, b in zip(sl, dd, bb):
    g = e['elementId']['guid']; x = d['details']; b = b['boundingBox3D']
    S[g[:4]] = dict(id=e['elementId'], poly=x['polygonOutline'], holes=x.get('holes') or [], z0=b['zMin'], z1=b['zMax'], f=d.get('floorIndex'))
json.dump(S, open(os.path.join(KIT, 'slabs_before_fixA.json'), 'w'), indent=0)
W = json.load(open(os.path.join(KIT, 'walls_before_fixA.json')))

def new_slab(poly, holes, top, comp=None, thick=None, mat=None):
    f = story_of(top - 0.01)
    d = {'level': top, 'referencePlaneLocation': 'Top', 'polygonCoordinates': poly, 'floorIndex': f}
    if holes: d['holes'] = holes
    if comp: d['structureType'] = 'Composite'; d['compositeId'] = comp
    else: d['structureType'] = 'Basic'; d['thickness'] = thick; d['buildingMaterialId'] = mat
    return d
created = []
def create(ds):
    r = t.call(P, 'CreateSlabs', {'slabsData': ds}); created.extend(r.get('elements', [])); return r

def covered(a, b, z0, z1):
    """辺 a-b が既存の壁（下端<=z0、上端>=z1、同じ線上 0.2 以内）で覆われているか"""
    ex, ey = b['x'] - a['x'], b['y'] - a['y']; L = (ex * ex + ey * ey) ** .5; ux, uy = ex / L, ey / L
    cov = 0
    for w in W:
        if w['z0'] > z0 + 0.01 or w['z1'] < z1 - 0.01: continue
        p, q = w['a'], w['b']
        d1 = abs((p['x'] - a['x']) * uy - (p['y'] - a['y']) * ux); d2 = abs((q['x'] - a['x']) * uy - (q['y'] - a['y']) * ux)
        if d1 > 0.21 or d2 > 0.21: continue
        s1 = (p['x'] - a['x']) * ux + (p['y'] - a['y']) * uy; s2 = (q['x'] - a['x']) * ux + (q['y'] - a['y']) * uy
        cov += max(0, min(L, max(s1, s2)) - max(0, min(s1, s2)))
    return cov >= 0.9 * L
def edge_walls(poly, z0, z1):
    """多角形の各辺に、覆われていなければ内側 0.1 に厚さ 0.2 の RC 壁（z0〜z1）"""
    n = len(poly); cx = sum(p['x'] for p in poly) / n; cy = sum(p['y'] for p in poly) / n
    out = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a['x'], a['y']) == (b['x'], b['y']) or covered(a, b, z0, z1): continue
        ex, ey = b['x'] - a['x'], b['y'] - a['y']; L = (ex * ex + ey * ey) ** .5; nx, ny = -ey / L, ex / L
        mx, my = (a['x'] + b['x']) / 2, (a['y'] + b['y']) / 2
        if (cx - mx) * nx + (cy - my) * ny < 0: nx, ny = -nx, -ny
        f = story_of(z0 + 0.001)
        out.append({'begCoordinate': {'x': a['x'] + nx * 0.1, 'y': a['y'] + ny * 0.1}, 'endCoordinate': {'x': b['x'] + nx * 0.1, 'y': b['y'] + ny * 0.1},
                    'floorIndex': f, 'zCoordinate': z0 - ST[f], 'height': z1 - z0, 'thickness': 0.2, 'structureType': 'Basic',
                    'buildingMaterialId': CONC, 'referenceLineLocation': 'Center'})
    return out

log = []; walls_new = []
# 1) そのまま屋根の板（厚さ 0.3）にする
mods = [{'elementId': S[k]['id'], 'structureType': 'Composite', 'compositeId': ROOF, 'referencePlaneLocation': 'Top', 'zCoordinate': S[k]['z1']} for k in ('D470', '5AD4', '553B')]
# 2) 上に屋根の板が既にある厚い塊：消して、下端に天井、縁に壁（下端〜上の板の下）
dels = []
for k, top_board in (('C519', 7.2), ('ACBA', 6.5), ('75DD', 3.0)):
    s = S[k]; dels.append(s['id'])
    create([new_slab(s['poly'], s['holes'], s['z0'] + 0.05, comp=CEIL)])
    walls_new += edge_walls(s['poly'], s['z0'], top_board); log.append((k, 'del+ceil', s['z0'], top_board))
# 3) 7D9A（RF の上の 0.7 の塊）：上 0.3 を屋根の板に、下は縁の壁
s = S['7D9A']
mods.append({'elementId': s['id'], 'structureType': 'Composite', 'compositeId': ROOF, 'referencePlaneLocation': 'Top', 'zCoordinate': s['z1']})
walls_new += edge_walls(s['poly'], s['z0'], s['z1'] - 0.3); log.append(('7D9A', 'roof+edge', s['z0'], s['z1'] - 0.3))
# 4) 2階の床（4EFD）と車庫上（4783）：上 0.3 を床の板に、下端に天井
for k in ('4EFD', '4783'):
    s = S[k]
    mods.append({'elementId': s['id'], 'structureType': 'Composite', 'compositeId': FL2, 'referencePlaneLocation': 'Top', 'zCoordinate': s['z1']})
    create([new_slab(s['poly'], s['holes'], s['z0'] + 0.05, comp=CEIL)]); log.append((k, 'floor+ceil', s['z0'], s['z1']))
r = t.call(P, 'ModifySlabs', {'slabsWithDetails': mods}); print('modify', r)
if dels: print('delete', t.call(P, 'DeleteElements', {'elements': [{'elementId': d} for d in dels]}))
if walls_new:
    r = t.call(P, 'CreateWalls', {'wallsData': walls_new}); print('edge walls', len(walls_new), str(r)[:200])
for l in log: print(l)
json.dump({'created_slabs': created, 'edge_walls': walls_new}, open(os.path.join(KIT, 'fixA_slabs_log.json'), 'w'), indent=0)
