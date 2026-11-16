"""修正A-0：直す前の壁の控えを取る → 同じフォルダの walls_before_fixA.json。

fixA_walls.py・fixA_slabs.py・fixA_found.py・layer_found.py がこれを読む。必ず fixA_walls.py より前に1回だけ流す
（後で流すと、縁の壁・基礎の壁まで「元の壁」に入ってしまう）。

元：実験では、この中身を1行のコマンドで流した（会話の記録から取り出してファイルにした。処理は同じ）。
キットの scripts/record/walls_before_fixA.json は、その時の実験のモデルの値（記録用。別のモデルには使えない）。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
OUT = os.path.join(HERE, 'walls_before_fixA.json')

if __name__ == '__main__':
    if os.path.exists(OUT) and '--force' not in sys.argv:
        sys.exit(f'{OUT} が既にある。取り直すなら --force（fixA_walls.py 以降を流した後に取り直さない）。')
    t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})   # 3D の窓のままだと壁が0本で返る
    ws = t.call(P, 'GetElementsByType', {'elementType': 'Wall'})['elements']
    dd = t.call(P, 'GetDetailsOfElements', {'elements': ws})['detailsOfElements']
    bb = t.call(P, 'Get3DBoundingBoxes', {'elements': ws})['boundingBoxes3D']
    out = []
    for e, d, b in zip(ws, dd, bb):
        x = d['details']; b = b['boundingBox3D']
        out.append(dict(g=e['elementId']['guid'], f=d.get('floorIndex'), t=x['begThickness'], a=x['begCoordinate'], b=x['endCoordinate'],
                        z0=round(b['zMin'], 3), z1=round(b['zMax'], 3), flip=x['flipped'], ref=x['referenceLineLocation'],
                        win=x['hasWindow'], door=x['hasDoor']))
    json.dump(out, open(OUT, 'w'), indent=0)
    for o in out:
        print(o['g'][:6], o['f'], o['t'], (o['a']['x'], o['a']['y']), (o['b']['x'], o['b']['y']), o['z0'], o['z1'], o['flip'])
    print(len(out), 'walls ->', OUT)
