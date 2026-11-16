"""基礎を専用の画層へ。外壁(1階)の下端を GL まで下げる。layer.py show|hide で表示切替。"""
import os, sys, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT); import tapir_http as t
P = int(os.environ.get('ARCHICAD_PORT', '19723'))
NAME = '架空_地中（基礎）'
def set_hidden(h):
    return t.call(P, 'CreateLayers', {'layerDataArray': [{'name': NAME, 'isHidden': h}], 'overwriteExisting': True})
if __name__ == '__main__':
    if sys.argv[1:] == ['hide']: print(set_hidden(True)); sys.exit()
    if sys.argv[1:] == ['show']: print(set_hidden(False)); sys.exit()
    r = set_hidden(False); print(r)
    lid = r['attributeIds'][0]['attributeId']
    la = t.call(P, 'GetAttributesByType', {'attributeType': 'Layer'})['attributes']
    idx = [a['index'] for a in la if a['attributeId']['guid'] == lid['guid']][0]; print('layer index', idx)
    L = json.load(open(os.path.join(KIT, 'fixA_found_log.json')))
    r = t.call(P, 'SetDetailsOfElements', {'elementsWithDetails': [{'elementId': e['elementId'], 'details': {'layerIndex': idx}} for e in L['found']]})
    print('found -> layer', sum(1 for x in r['executionResults'] if x.get('success')), len(L['found']))
    W = json.load(open(os.path.join(KIT, 'walls_before_fixA.json')))
    mods = [{'elementId': {'guid': w['g']}, 'bottomOffset': -0.1, 'height': round(w['z1'] - w['z0'] + 0.1, 4)}
            for w in W if w['f'] == 0 and w['t'] > 0.15 and w['z0'] < 0.01]
    r = t.call(P, 'ModifyWalls', {'wallsWithDetails': mods}); print('ext walls to GL', len(mods), r['executionResults'][:1])
    b = t.call(P, 'Get3DBoundingBoxes', {'elements': [{'elementId': m['elementId']} for m in mods[:3]]})['boundingBoxes3D']
    print([(round(x['boundingBox3D']['zMin'], 3), round(x['boundingBox3D']['zMax'], 3)) for x in b])
    print(t.call(P, 'SaveProject', {}))
