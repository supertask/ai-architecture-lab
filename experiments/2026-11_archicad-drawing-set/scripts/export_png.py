"""図面8枚を高解像度の PNG に書き出す（2×2 に拡大して撮って貼り合わせ）＋各図の文字を JSON に。点検用。

使い方：
    python export_png.py                 # 8枚 → <KIT>/out/png/hi_<図>.png と texts_<図>.json
    python export_png.py SA P1           # 一部だけ
    python export_png.py --out D:/x/     # 書き出し先を変える
図の記号：ES/EN/EE/EW＝立面（窓 S南/S北/S東/S西）、SA/SB＝断面（A-A/B-B）、P1/P2＝1階/2階平面。
必要：Pillow, numpy（例：uv run --with pillow --with numpy python export_png.py）。

元：実験の書き出しスクリプト。パス・ポート・平面の撮影範囲・文字の読み出し先を一般化した。
- 立面（E…）と平面（P…）では、地中の画層（layer_found.py）を隠す。断面（S…）だけ出す。最後に表示へ戻す。
- 平面は、大きな敷地の板のせいで FitInWindow が敷地全体に広がるので、壁の範囲 ± PLAN_MARGIN（既定 9.5 m）で撮る。
- SaveCurrentWindowAsImage は窓の大きさの画素でしか撮れない。範囲を4つに分けて SetZoom し、返ってきた zoom
  （窓の縦横比で広がる）から欲しい範囲だけ切り出して貼る。SetZoom の直後の1枚目は前の表示が写ることがあるので、
  3 秒待ってから2回撮って2枚目を使う。パスは絶対パスで渡す（相対だと書けない）。
- 貼り合わせた画像は、GL の線が1本か（つなぎ目のずれ）を見てから点検に回す。
"""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t
import layer_found
from PIL import Image
import numpy as np

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
MARGIN = float(os.environ.get('PLAN_MARGIN', '9.5'))
args = sys.argv[1:]
O = os.path.join(os.path.dirname(HERE), 'out', 'png')
if '--out' in args:
    i = args.index('--out'); O = args[i + 1]; del args[i:i + 2]
O = os.path.abspath(O).replace('\\', '/') + '/'
os.makedirs(O, exist_ok=True)

dbs = t.call(P, 'GetDatabases', {})['databases']
by = {d.get('name'): d['databaseId'] for d in dbs if d.get('type') == 'Section'}
NAMES = [('ES', 'S南'), ('EN', 'S北'), ('EE', 'S東'), ('EW', 'S西'), ('SA', 'A-A'), ('SB', 'B-B')]
V = [(k, by[n]) for k, n in NAMES if n in by] + [('P1', 0), ('P2', 1)]
missing = [n for _, n in NAMES if n not in by]
if missing: print('見つからない断面の窓:', missing)
only = args or [k for k, _ in V]


def plan_box():
    t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
    ws = t.call(P, 'GetElementsByType', {'elementType': 'Wall'})['elements']
    xs, ys = [], []
    for d in t.call(P, 'GetDetailsOfElements', {'elements': ws})['detailsOfElements']:
        for k in ('begCoordinate', 'endCoordinate'):
            if k in d['details']: xs.append(d['details'][k]['x']); ys.append(d['details'][k]['y'])
    return {'xMin': min(xs) - MARGIN, 'yMin': min(ys) - MARGIN, 'xMax': max(xs) + MARGIN, 'yMax': max(ys) + MARGIN}


PB = plan_box() if any(k.startswith('P') for k in only) else None
try:
    for k, ref in V:
        if k not in only: continue
        layer_found.set_hidden(k[0] in 'EP')   # 立面・平面では地中を隠す。断面だけ出す
        if isinstance(ref, int):
            t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': ref}); time.sleep(2)
            t.call(P, 'SetZoom', {'zoomBox': PB}); time.sleep(1.5)
        else:
            t.call(P, 'ChangeWindow', {'databaseId': ref}); time.sleep(2); t.call(P, 'FitInWindow', {}); time.sleep(1.5)
        t.call(P, 'SaveCurrentWindowAsImage', {'imageFilePath': O + 'tmp_fit.png'}); time.sleep(1.5)
        r = t.call(P, 'SaveCurrentWindowAsImage', {'imageFilePath': O + 'tmp_fit.png'}); z = r['zoom']
        im = Image.open(O + 'tmp_fit.png').convert('RGB')
        a = np.asarray(im.convert('L')); ys, xs = np.where(a < 235); W, H = im.size
        if len(xs) == 0: print(k, '真っ白。窓が開いていないか、表示が更新されていない'); continue
        X = lambda px: z['xMin'] + (z['xMax'] - z['xMin']) * px / W
        Y = lambda py: z['yMax'] - (z['yMax'] - z['yMin']) * py / H
        x0, x1, y0, y1 = X(xs.min()) - 0.5, X(xs.max()) + 0.5, Y(ys.max()) - 0.5, Y(ys.min()) + 0.5
        cw, ch = (x1 - x0) / 2, (y1 - y0) / 2
        tiles = []
        for j in range(2):
            row = []
            for i in range(2):
                zb = {'xMin': x0 + i * cw, 'xMax': x0 + (i + 1) * cw, 'yMin': y1 - (j + 1) * ch, 'yMax': y1 - j * ch}
                t.call(P, 'SetZoom', {'zoomBox': zb}); time.sleep(3)
                t.call(P, 'SaveCurrentWindowAsImage', {'imageFilePath': O + 'tmp_t.png'}); time.sleep(1.5)
                rr = t.call(P, 'SaveCurrentWindowAsImage', {'imageFilePath': O + 'tmp_t.png'}); zz = rr['zoom']
                if abs(zz['xMin'] - zb['xMin']) > 0.6 * (zb['xMax'] - zb['xMin']): print('WARN zoom', zb, zz)
                ti = Image.open(O + 'tmp_t.png').convert('RGB'); TW, TH = ti.size
                px = lambda x: (x - zz['xMin']) / (zz['xMax'] - zz['xMin']) * TW
                py = lambda y: (zz['yMax'] - y) / (zz['yMax'] - zz['yMin']) * TH
                row.append(ti.crop((int(px(zb['xMin'])), int(py(zb['yMax'])), int(px(zb['xMax'])), int(py(zb['yMin'])))))
            tiles.append(row)
        w = tiles[0][0].width + tiles[0][1].width; h = tiles[0][0].height + tiles[1][0].height
        big = Image.new('RGB', (w, h), 'white')
        big.paste(tiles[0][0], (0, 0)); big.paste(tiles[0][1], (tiles[0][0].width, 0))
        big.paste(tiles[1][0], (0, tiles[0][0].height)); big.paste(tiles[1][1], (tiles[1][0].width, tiles[0][1].height))
        big.save(O + f'hi_{k}.png'); print(k, big.size)
        # 文字（点検で、レベル・寸法の数字をモデルと照合するため）
        p = {'elementType': 'Text'}
        if not isinstance(ref, int): p['databases'] = [{'databaseId': ref}]
        els = t.call(P, 'GetElementsByType', p)['elements']
        det = t.call(P, 'GetDetailsOfElements', {'elements': els})['detailsOfElements'] if els else []
        tx = []
        for d in det:
            if isinstance(ref, int) and d.get('floorIndex') != ref: continue
            x = d.get('details', {}); tx.append(x.get('text') or x.get('content') or str(x)[:120])
        json.dump(tx, open(O + f'texts_{k}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(k, 'texts', len(tx))
finally:
    layer_found.set_hidden(False)
