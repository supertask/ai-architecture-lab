"""修正A：複合構造（架空の家用）を作る。結果は同じフォルダの fixA_comps.json"""
import os, sys, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT); import tapir_http as t
P = t.default_port()
bm = {a['index']: a['attributeId'] for a in t.call(P, 'GetAttributesByType', {'attributeType': 'BuildingMaterial'})['attributes']}
solid = t.call(P, 'GetAttributesByType', {'attributeType': 'Line'})['attributes'][0]['attributeId']
def comp(name, use, skins):
    sk = [{'type': ty, 'buildingMaterialId': {'attributeId': bm[b]}, 'framePen': 1, 'thickness': th} for ty, b, th in skins]
    sep = [{'lineTypeId': {'attributeId': solid}, 'linePen': 1} for _ in range(len(sk) + 1)]
    return {'name': name, 'useWith': use, 'skins': sk, 'separators': sep}
EXT = [('Core', 3, 0.15), ('Other', 30, 0.035), ('Finish', 15, 0.015)]
D = [
 comp('架空_外壁 RC打放し150 断熱35 PB', ['Wall'], EXT),
 comp('架空_外壁(逆) PB 断熱35 RC打放し150', ['Wall'], EXT[::-1]),
 comp('架空_間仕切 PB12.5 LGS95 PB12.5', ['Wall'], [('Finish', 15, 0.0125), ('Core', 61, 0.095), ('Finish', 15, 0.0125)]),
 comp('架空_屋根 押えコン60 断熱30 防水10 RC200', ['Slab'], [('Finish', 5, 0.06), ('Other', 64, 0.03), ('Other', 28, 0.01), ('Core', 3, 0.2)]),
 comp('架空_2階床 フローリング15 置床85 RC200', ['Slab'], [('Finish', 34, 0.015), ('Other', 63, 0.085), ('Core', 3, 0.2)]),
 comp('架空_天井 LGS40 PB9.5', ['Slab'], [('Other', 62, 0.0405), ('Finish', 21, 0.0095)]),
 comp('架空_1階床 フローリング15 断熱85 RC土間150 砕石100', ['Slab'], [('Finish', 34, 0.015), ('Other', 64, 0.085), ('Core', 3, 0.15), ('Other', 60, 0.1)]),
]
r = t.call(P, 'CreateComposites', {'compositeDataArray': D, 'overwriteExisting': True})
print(r)
ids = {d['name']: x['attributeId'] for d, x in zip(D, r['attributeIds'])}
json.dump(ids, open(os.path.join(KIT, 'fixA_comps.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
