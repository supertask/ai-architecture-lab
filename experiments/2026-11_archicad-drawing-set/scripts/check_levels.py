"""点検の1段目（数値）：書き出した各図の文字（out/png/texts_<図>.json）から、レベル表記・通り芯の名前を抜き出し、
モデルの値・図どうしで食い違いがないかを表にする。Archicad は読むだけ（--offline なら触らない）。

使い方：
    python check_levels.py                       # 期待値をモデルから読む（1FL・2FL・RFL の階の高さ、全要素の最高高さ）
    python check_levels.py --offline --expect "1FL=100,2FL=3250,軒高=6900,最高高さ=7600"
    python check_levels.py --dir D:/x/png/       # texts_*.json の場所（既定 <KIT>/out/png/）

見るもの：
- 「▽名称=GL+数値」「△GL」などの書き方を全部の図から集め、同じ名前の値が図ごとに違わないか、期待値と合うか
- 同じレベルの書き方の揺れ（「GL±0」と「GL+0」、「RFL」と「軒高」など）
- 通り芯の名前（X1… / Y1…）が grid.json にある物だけか
寸法の合計＝全長、重なりは、この表のあとに画像と座標で確かめる（skills/inspection.md）。
"""
import os, sys, re, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); return args[i + 1]
    return default
D = opt('--dir', os.path.join(os.path.dirname(HERE), 'out', 'png'))
LEVEL = re.compile(r'([▽△])\s*([^\s=＝]+?)\s*[=＝]\s*GL\s*([+\-±＋－])?\s*([\d,，]+)?')
GRID = re.compile(r'^\s*([XY]\d{1,2})\s*$')

expect = {}
if opt('--expect'):
    for kv in opt('--expect').split(','):
        k, v = kv.split('='); expect[k.strip()] = int(v)
if '--offline' not in args:
    import tapir_http as t
    P = t.default_port()
    for s in t.call(P, 'GetStories', {})['stories']:
        # 作図ルールでは最上階（RFL）を「軒高」と書く
        expect.setdefault('軒高' if s['name'] == 'RFL' else s['name'], round(s['level'] * 1000))
    t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
    els = []
    for ty in ('Wall', 'Slab', 'Roof'):
        try: els += t.call(P, 'GetElementsByType', {'elementType': ty})['elements']
        except Exception: pass
    bb = [b['boundingBox3D'] for b in t.call(P, 'Get3DBoundingBoxes', {'elements': els})['boundingBoxes3D'] if 'boundingBox3D' in b]
    expect.setdefault('最高高さ', round(max(b['zMax'] for b in bb) * 1000))
print('期待値（mm, GL 基準）:', expect)

grid_names = set()
for gpath in (os.path.join(os.path.dirname(HERE), 'work', 'grid.json'), os.path.join(HERE, 'grid.json')):
    if os.path.exists(gpath):
        g = json.load(open(gpath, encoding='utf-8'))
        try:
            grid_names = {x['name'] for k in ('X', 'Y') for x in g.get(k, [])}
        except (TypeError, KeyError):
            print('grid.json の形がキットと違う。先に python scripts/check_grid.py でそろえる'); grid_names = set()
        break

seen = {}   # 名前 -> {図: 値}
bad = []
for f in sorted(glob.glob(os.path.join(D, 'texts_*.json'))):
    k = os.path.basename(f)[6:-5]
    for s in json.load(open(f, encoding='utf-8')):
        s = str(s)
        for m in LEVEL.finditer(s):
            name, sign, num = m.group(2), m.group(3) or '+', m.group(4)
            v = 0 if num is None else int(num.replace(',', '').replace('，', '')) * (-1 if sign in '-－' else 1)
            seen.setdefault(name, {})[k] = (v, m.group(0))
        gm = GRID.match(s)
        if gm and grid_names and gm.group(1) not in grid_names:
            bad.append((k, f'grid.json に無い通り芯 {gm.group(1)}'))
for name, per in sorted(seen.items()):
    vals = {v for v, _ in per.values()}
    flag = ''
    if len(vals) > 1: flag += ' ← 図ごとに値が違う'
    if name in expect and any(abs(v - expect[name]) > 1 for v in vals): flag += f' ← モデルは {expect[name]}'
    spell = {txt for _, txt in per.values()}
    print(f'{name}: ' + ', '.join(f'{k}={v}' for k, (v, _) in sorted(per.items())) + flag)
    if len(spell) > 1: print('   書き方の揺れ:', sorted(spell))
missing = [n for n in expect if n not in seen]
if missing: print('どの図にも無いレベル:', missing)
for b in bad: print('NG', *b)
