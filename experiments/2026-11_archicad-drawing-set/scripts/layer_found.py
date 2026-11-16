"""地中（基礎・1階の床の層・敷地と水盤の板）を専用の画層へ移し、1階の外壁の下端を GL まで下げる。

使い方：
    python layer_found.py          # 画層を作って移す（fixA_raise.py の後に1回）
    python layer_found.py hide     # 地中の画層を隠す（立面・平面を書き出す時。export_png.py が自動で切り替える）
    python layer_found.py show     # 表示に戻す（断面を書き出す時・作業中）

なぜ：立面や平面に、GL より下の基礎・床の層・敷地の板の輪郭が線で出る。2D の白い塗りでは隠せない
（断面・立面の窓では 2D の塗りがモデルの線の下に描かれる）ので、画層ごと隠す。
- 移すもの：fixA_found.py が作った基礎の壁と1階の床（fixA_found_log.json）、上端が GL 以下のスラブ（敷地・水盤）。
  元の実験では、基礎はこのスクリプトで、床と敷地・水盤はあとから2回の短いコマンドで移した（ここに1本にまとめた）。
- 1階の外壁の下端を GL まで下げる（-RAISE、既定 0.1 = fixA_raise.py で上げた分）。基礎を隠した時に壁と地面の間にすき間が見えないように。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
NAME = '架空_地中（基礎）'
RAISE = float(os.environ.get('RAISE', '0.1'))


def set_hidden(h):
    return t.call(P, 'CreateLayers', {'layerDataArray': [{'name': NAME, 'isHidden': h}], 'overwriteExisting': True})


if __name__ == '__main__':
    if sys.argv[1:] == ['hide']: print(set_hidden(True)); sys.exit()
    if sys.argv[1:] == ['show']: print(set_hidden(False)); sys.exit()
    r = set_hidden(False); print(r)
    lid = r['attributeIds'][0]['attributeId']
    la = t.call(P, 'GetAttributesByType', {'attributeType': 'Layer'})['attributes']
    idx = [a['index'] for a in la if a['attributeId']['guid'] == lid['guid']][0]; print('layer index', idx)
    L = json.load(open(os.path.join(HERE, 'fixA_found_log.json')))
    t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
    sl = t.call(P, 'GetElementsByType', {'elementType': 'Slab'})['elements']
    sb = t.call(P, 'Get3DBoundingBoxes', {'elements': sl})['boundingBoxes3D']
    below = [e for e, b in zip(sl, sb) if b['boundingBox3D']['zMax'] <= 0.001]   # 敷地・水盤（GL 以下）
    els = L['found'] + L['floor'] + below
    r = t.call(P, 'SetDetailsOfElements', {'elementsWithDetails': [{'elementId': e['elementId'], 'details': {'layerIndex': idx}} for e in els]})
    print('-> layer', sum(1 for x in r['executionResults'] if x.get('success')), '/', len(els),
          f'(基礎 {len(L["found"])}, 1階床 {len(L["floor"])}, GL 以下の板 {len(below)})')
    W = json.load(open(os.path.join(HERE, 'walls_before_fixA.json')))
    mods = [{'elementId': {'guid': w['g']}, 'bottomOffset': -RAISE, 'height': round(w['z1'] - w['z0'] + RAISE, 4)}
            for w in W if w['f'] == 0 and w['t'] > 0.15 and w['z0'] < 0.01]
    r = t.call(P, 'ModifyWalls', {'wallsWithDetails': mods}); print('ext walls to GL', len(mods), r['executionResults'][:1])
    b = t.call(P, 'Get3DBoundingBoxes', {'elements': [{'elementId': m['elementId']} for m in mods[:3]]})['boundingBoxes3D']
    print('下端が 0（GL）になったか:', [(round(x['boundingBox3D']['zMin'], 3), round(x['boundingBox3D']['zMax'], 3)) for x in b])
    print(t.call(P, 'SaveProject', {}))
