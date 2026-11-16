"""修正A-3：1階の床（部屋ごと）と基礎（外壁の下）を足す。"""
import os, sys, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT); import tapir_http as t
P = int(os.environ.get('ARCHICAD_PORT', '19723'))
C = json.load(open(os.path.join(KIT, 'fixA_comps.json'), encoding='utf-8'))
FL1 = C['架空_1階床 フローリング15 断熱85 RC土間150 砕石100']
bm = {a['name']: a['attributeId'] for a in t.call(P, 'GetAttributesByType', {'attributeType': 'BuildingMaterial'})['attributes']}
CONC = bm['コンクリート']
zs = t.call(P, 'GetElementsByType', {'elementType': 'Zone'})['elements']
zd = t.call(P, 'GetDetailsOfElements', {'elements': zs})['detailsOfElements']
data = []
for d in zd:
    if d.get('floorIndex') != 0: continue
    x = d['details']; name = x.get('name', '')
    poly = x.get('polygonOutline') or x.get('polygonCoordinates')
    print(name, len(poly))
    if '水盤' in name: continue
    if '車庫' in name:  # 車庫は土間コンクリート
        data.append({'level': 0.0, 'referencePlaneLocation': 'Top', 'polygonCoordinates': poly, 'floorIndex': 0,
                     'structureType': 'Basic', 'thickness': 0.15, 'buildingMaterialId': CONC})
    else:
        data.append({'level': 0.0, 'referencePlaneLocation': 'Top', 'polygonCoordinates': poly, 'floorIndex': 0,
                     'structureType': 'Composite', 'compositeId': FL1})
r = t.call(P, 'CreateSlabs', {'slabsData': data}); print('floor slabs', len(r['elements']))
# 基礎：1階の外壁（厚さ 0.2 の壁）の下に、立上り（厚さ 0.2、1FL-0.75〜1FL）と底盤（幅 0.6、-0.95〜-0.75）
W = json.load(open(os.path.join(KIT, 'walls_before_fixA.json')))
fw = []
for w in W:
    if w['f'] != 0 or w['t'] < 0.15 or w['z0'] > 0.01: continue
    for z, h, th in ((-0.75, 0.75, 0.2), (-0.95, 0.2, 0.6)):
        fw.append({'begCoordinate': w['a'], 'endCoordinate': w['b'], 'floorIndex': 0, 'zCoordinate': z, 'height': h, 'thickness': th,
                   'structureType': 'Basic', 'buildingMaterialId': CONC, 'referenceLineLocation': 'Center'})
r2 = t.call(P, 'CreateWalls', {'wallsData': fw}); print('foundation walls', len(r2['elements']))
json.dump({'floor': r['elements'], 'found': r2['elements']}, open(os.path.join(KIT, 'fixA_found_log.json'), 'w'))
