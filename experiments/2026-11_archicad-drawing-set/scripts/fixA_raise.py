"""修正A-4：家ごと +0.1 上げて 1FL = GL+100 にする（敷地・水盤の板は元の高さに戻す）。

使い方：
    python fixA_raise.py          # +0.1
    python fixA_raise.py 0.15     # 上げる量を変える（m）
fixA_found.py の後、layer_found.py の前に1回だけ流す（2回流すと 2回上がる）。

元：実験では、この中身を2回の短いコマンドで流した（会話の記録から取り出してファイルにした）。
元は、戻すスラブを要素 ID で指定していた。ここでは「上げる前に上端が GL 以下だったスラブ」を探して戻す（同じ3枚になる）。
- SetStories に全部の階の項目（index, floorId, dispOnSections, level, height, name）を渡すと、要素は階と一緒に動く。
  一部の項目だけを渡すと失敗した（"Failed to change story height" など）。
- 地面・水盤の板は ModifySlabs の zCoordinate（参照面 Top の絶対高さ）で元に戻す。
- 終わりに全要素の最高・最低の高さを表示して SaveProject。実験では最高 GL+7600、最低 GL-850 になった。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
D = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1

t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
sl = t.call(P, 'GetElementsByType', {'elementType': 'Slab'})['elements']
sb = t.call(P, 'Get3DBoundingBoxes', {'elements': sl})['boundingBoxes3D']
ground = [(e['elementId'], b['boundingBox3D']['zMax']) for e, b in zip(sl, sb) if b['boundingBox3D']['zMax'] <= 0.001]
print('GL 以下の板（戻す）', len(ground), [round(z, 3) for _, z in ground])

st = t.call(P, 'GetStories', {})
new = [{k: v for k, v in s.items() if k in ('index', 'floorId', 'dispOnSections', 'level', 'height', 'name')} for s in st['stories']]
for s in new: s['level'] = round(s['level'] + D, 4)
print(t.call(P, 'SetStories', {'stories': new}))
print([(s['name'], s['level']) for s in t.call(P, 'GetStories', {})['stories']])

if ground:
    mods = [{'elementId': g, 'referencePlaneLocation': 'Top', 'zCoordinate': z} for g, z in ground]
    print('restore', t.call(P, 'ModifySlabs', {'slabsWithDetails': mods}))
els = []
for ty in ('Wall', 'Slab', 'Window', 'Door', 'Zone', 'Stair'):
    try: els += t.call(P, 'GetElementsByType', {'elementType': ty})['elements']
    except Exception as e: print(ty, str(e)[:100])
bb = [b['boundingBox3D'] for b in t.call(P, 'Get3DBoundingBoxes', {'elements': els})['boundingBoxes3D'] if 'boundingBox3D' in b]
print('zmax', round(max(b['zMax'] for b in bb), 3), 'zmin', round(min(b['zMin'] for b in bb), 3))
print(t.call(P, 'SaveProject', {}))
