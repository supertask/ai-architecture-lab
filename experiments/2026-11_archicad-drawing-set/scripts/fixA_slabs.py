"""修正A-2：床・屋根を複合構造に、厚い塊の屋根を「屋根の板＋天井＋縁の壁」に分ける。

使い方：
    python fixA_slabs.py           # 振り分けの計画を表示するだけ（何も変えない）
    python fixA_slabs.py --apply   # 計画どおりに直す
前に fixA_comps.py（複合構造）と fixA_snapshot.py（壁の控え）を流しておく。

元の実験のスクリプトは、直すスラブを要素 ID（そのモデルだけの値）で指定していた。公開版は、同じ振り分けを
高さと平面の範囲の規則で行う（再構成）。実験の時に控えたスラブの値にこの規則を当てると、元のスクリプト
（と、その直後に手で行った1枚の直し）と同じ振り分けになることを確かめた。Archicad では流していない。
--apply の前に、表示された計画を必ず見て確かめる。

振り分けの規則（高さは m、直す前の値）：
  0. 上端が GL 以下（z1 <= 0.01）：地面・水盤 → 触らない
  1. 上端に屋根の板（厚さ 0.28〜0.32、上端が同じ、平面でこの板の 9 割以上を覆う）が重なっている厚い塊
     → 消して、下端 +0.05 に天井スラブ、縁に厚さ 0.2 の RC 壁（下端〜板の下端）
  1a. 1 のうち、輪郭が円弧を細かく割った多角形（0.2 m 未満の辺が 9 本以上）のもの
     → 縁の壁が細切れになるので、壁にせず、下端〜板の下端の RC の板（Basic）に作り直す
     （実験では一度 1 で作ってから、この形に直した）
  2. 厚さ 0.28〜0.32 ＝ 屋根の板 → 屋根の複合構造に（上端は保つ）
  3. 上端が 2階以上・最上階未満の階の高さと一致する厚い板 ＝ 2階の床 → 床の複合構造（上端は保つ）＋ 下端 +0.05 に天井
  4. それ以外の厚い板（屋根の上の塊）→ 上 0.3 を屋根の複合構造に、下は縁の壁（下端〜上端 -0.3）

実験のモデルでの振り分け（参考）：0 が3枚、1 が2枚、1a が1枚、2 が3枚、3 が2枚、4 が1枚。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
APPLY = '--apply' in sys.argv
C = json.load(open(os.path.join(HERE, 'fixA_comps.json'), encoding='utf-8'))
ROOF, FL2, CEIL = (C['架空_屋根 押えコン60 断熱30 防水10 RC200'], C['架空_2階床 フローリング15 置床85 RC200'], C['架空_天井 LGS40 PB9.5'])
bm = {a['name']: a['attributeId'] for a in t.call(P, 'GetAttributesByType', {'attributeType': 'BuildingMaterial'})['attributes']}
CONC = bm['コンクリート']
ST = {s['index']: s['level'] for s in t.call(P, 'GetStories', {})['stories']}
def story_of(z): return max(i for i, l in ST.items() if l <= z + 1e-6)

t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})   # 3D の窓のままだと要素が0で返る
sl = t.call(P, 'GetElementsByType', {'elementType': 'Slab'})['elements']
dd = t.call(P, 'GetDetailsOfElements', {'elements': sl})['detailsOfElements']
bb = t.call(P, 'Get3DBoundingBoxes', {'elements': sl})['boundingBoxes3D']
S = {}
for e, d, b in zip(sl, dd, bb):
    g = e['elementId']['guid']; x = d['details']; b = b['boundingBox3D']
    S[g] = dict(id=e['elementId'], poly=x['polygonOutline'], holes=x.get('holes') or [], z0=b['zMin'], z1=b['zMax'],
                box=(b['xMin'], b['yMin'], b['xMax'], b['yMax']), f=d.get('floorIndex'))
json.dump(S, open(os.path.join(HERE, 'slabs_before_fixA.json'), 'w'), indent=0)
W = json.load(open(os.path.join(HERE, 'walls_before_fixA.json')))


def is_board(s): return 0.28 <= s['z1'] - s['z0'] <= 0.32


def cover(a, b):
    """平面の範囲 a のうち、b が覆う割合"""
    w = max(0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    A = (a[2] - a[0]) * (a[3] - a[1])
    return w * h / A if A > 0 else 0


def board_in_top(g):
    """この塊の上端に重なっている屋根の板の下端（無ければ None）"""
    s = S[g]
    c = [o['z0'] for h, o in S.items() if h != g and is_board(o) and abs(o['z1'] - s['z1']) < 0.02
         and o['z0'] > s['z0'] + 0.05 and cover(s['box'], o['box']) >= 0.9]
    return min(c) if c else None


def short_edges(p):
    n = len(p)
    return sum(1 for i in range(n) if ((p[i]['x'] - p[(i + 1) % n]['x']) ** 2 + (p[i]['y'] - p[(i + 1) % n]['y']) ** 2) ** .5 < 0.2)


levels = [l for i, l in sorted(ST.items()) if i >= 1][:-1]   # 2階以上・最上階未満
plan = []   # (guid, 規則, 板の下端, 説明)
for g, s in S.items():
    if s['z1'] <= 0.01: plan.append((g, '0', None, '地面・水盤（触らない）')); continue
    top = board_in_top(g)
    if top is not None:
        if short_edges(s['poly']) > 8:
            plan.append((g, '1a', top, f'円弧の塊 → RC の板 {s["z0"]:.2f}〜{top:.2f} に作り直す')); continue
        plan.append((g, '1', top, f'上に屋根の板 → 消す＋天井＋縁の壁 {s["z0"]:.2f}〜{top:.2f}')); continue
    if is_board(s): plan.append((g, '2', None, '屋根の板 → 屋根の複合構造')); continue
    if any(abs(s['z1'] - l) < 0.02 for l in levels):
        plan.append((g, '3', None, '2階の床 → 床の複合構造＋天井')); continue
    plan.append((g, '4', None, f'屋根の上の塊 → 上 0.3 を屋根、縁の壁 {s["z0"]:.2f}〜{s["z1"] - 0.3:.2f}'))
for g, k, _, why in sorted(plan, key=lambda p: (p[1], S[p[0]]['z1'])):
    s = S[g]; print(f'[{k}] z {s["z0"]:.3f}〜{s["z1"]:.3f} 範囲 {[round(v, 2) for v in s["box"]]} 頂点 {len(s["poly"])} : {why}')
if not APPLY:
    sys.exit('（計画だけ。直すなら --apply）')


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


mods, dels, walls_new, log = [], [], [], []
for g, k, top, why in plan:
    s = S[g]
    if k == '1':
        dels.append(s['id'])
        create([new_slab(s['poly'], s['holes'], s['z0'] + 0.05, comp=CEIL)])
        walls_new += edge_walls(s['poly'], s['z0'], top)
    elif k == '1a':
        dels.append(s['id'])
        create([new_slab(s['poly'], s['holes'], top, thick=round(top - s['z0'], 4), mat=CONC)])
    elif k == '2':
        mods.append({'elementId': s['id'], 'structureType': 'Composite', 'compositeId': ROOF, 'referencePlaneLocation': 'Top', 'zCoordinate': s['z1']})
    elif k == '3':
        mods.append({'elementId': s['id'], 'structureType': 'Composite', 'compositeId': FL2, 'referencePlaneLocation': 'Top', 'zCoordinate': s['z1']})
        create([new_slab(s['poly'], s['holes'], s['z0'] + 0.05, comp=CEIL)])
    elif k == '4':
        mods.append({'elementId': s['id'], 'structureType': 'Composite', 'compositeId': ROOF, 'referencePlaneLocation': 'Top', 'zCoordinate': s['z1']})
        walls_new += edge_walls(s['poly'], s['z0'], s['z1'] - 0.3)
    else:
        continue
    log.append((g[:8], k, round(s['z0'], 3), round(s['z1'], 3)))
if mods: print('modify', t.call(P, 'ModifySlabs', {'slabsWithDetails': mods}))
if dels: print('delete', t.call(P, 'DeleteElements', {'elements': [{'elementId': d} for d in dels]}))
if walls_new:
    r = t.call(P, 'CreateWalls', {'wallsData': walls_new}); print('edge walls', len(walls_new), str(r)[:200])
for l in log: print(l)
json.dump({'created_slabs': created, 'edge_walls': walls_new}, open(os.path.join(HERE, 'fixA_slabs_log.json'), 'w'), indent=0)
print('次：fixA_found.py。区切りごとに SaveProject（python check_connection.py --save）')
