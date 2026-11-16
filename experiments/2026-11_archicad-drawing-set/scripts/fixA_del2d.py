"""修正A-5：8枚の図の 2D（前に AI が描いた線・塗り・文字・寸法など）を全部消す。モデルを直した後、描き直す前に流す。

使い方：
    python fixA_del2d.py          # 消す数を数えるだけ
    python fixA_del2d.py --apply  # 消して SaveProject

なぜ：前の回で AI が切断面の上に塗った灰色の塗りが、モデルに足した層（断熱・仕上）を隠す。古い寸法・レベルも
モデルを直すと合わなくなる。
- 対象：断面の窓 S南・S東・S北・S西・A-A・B-B（GetDatabases の name で探す）と、平面図の 1階・2階に置いた 2D。
- ゾーン（部屋）は消さない。
元：実験のスクリプト。元は立面の窓を ID で、平面を別ファイルの ID で指定していた。ここでは窓を名前で探し、
平面は平面図の窓に切り替えて読む形にした（平面の部分は再構成。Archicad では流していない）。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
APPLY = '--apply' in sys.argv
VIEWS = ['S南', 'S東', 'S北', 'S西', 'A-A', 'B-B']
TYPES = ['Line', 'PolyLine', 'Hatch', 'Text', 'Dimension', 'Circle', 'Arc', 'Label', 'Spline', 'Hotspot',
         'LevelDimension', 'RadialDimension', 'AngleDimension']


def collect(dbid=None):
    els = []
    for ty in TYPES:
        p = {'elementType': ty}
        if dbid is not None: p['databases'] = [{'databaseId': dbid}]
        try: els += t.call(P, 'GetElementsByType', p)['elements']
        except Exception: pass   # その種類が無い・数えられない版もある
    return els


log = {}
dbs = t.call(P, 'GetDatabases', {})['databases']
for name in VIEWS:
    m = [d for d in dbs if d.get('type') == 'Section' and d.get('name') == name]
    if not m: print(name, 'が見つからない'); continue
    els = collect(m[0]['databaseId'])
    if APPLY and els: t.call(P, 'DeleteElements', {'elements': els})
    log[name] = len(els); print(name, len(els))
# 平面図：窓を平面図にして読む（GetElementsByType は今の窓のデータベースを読む）。1階・2階に置いた物だけ
t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
els = collect()
if els:
    det = t.call(P, 'GetDetailsOfElements', {'elements': els})['detailsOfElements']
    els = [e for e, x in zip(els, det) if x.get('floorIndex') in (0, 1)]
if APPLY and els: t.call(P, 'DeleteElements', {'elements': els})
log['PLAN'] = len(els); print('PLAN', len(els))
if APPLY:
    json.dump(log, open(os.path.join(HERE, 'fixA_del2d.json'), 'w'))
    print(t.call(P, 'SaveProject', {}))
else:
    print('（数えただけ。消すなら --apply）')
