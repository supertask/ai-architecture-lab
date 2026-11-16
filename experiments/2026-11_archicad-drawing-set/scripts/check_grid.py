"""通り芯ファイル（<KIT>/work/grid.json）を確かめ、キットの形にそろえる。Archicad には触らない。

使い方：
    python check_grid.py                 # work/grid.json を読む → 形が違えばそろえて書き直す（元は grid_raw.json に残す）
    python check_grid.py D:/x/grid.json  # 場所を指定

キットの形（scripts/grid.json と同じ）：
    {"unit": "m", "X": [{"name": "X1", "coord": 0.1}, ...], "Y": [{"name": "Y1", "coord": 0.1}, ...]}
X 通り＝南北に走る線（x 座標）、Y 通り＝東西に走る線（y 座標）。単位 m。
受け付ける形の例：{"X": {"X1": 0.1, ...}}、{"X": [["X1", 0.1], ...]}、{"X": [{"label": "X1", "x": 0.1}]}、
{"grids": [{"name": "X1", "axis": "X", "coord": 0.1}, ...]}。mm で書かれていそうな時（値が 100 を超える）は m に直す。
終了コード：0＝OK、1＝読めない・足りない。
"""
import os, sys, json, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'work', 'grid.json')


def items(v, axis):
    out = []
    if isinstance(v, dict):
        v = [{'name': k, 'coord': c} for k, c in v.items()]
    for x in v or []:
        if isinstance(x, (list, tuple)) and len(x) >= 2:
            out.append((str(x[0]), float(x[1])))
        elif isinstance(x, dict):
            name = x.get('name') or x.get('label') or x.get('id')
            c = next((x[k] for k in ('coord', 'pos', 'position', 'value', axis.lower(), 'x', 'y') if k in x
                      and isinstance(x[k], (int, float))), None)
            if name is not None and c is not None:
                out.append((str(name), float(c)))
    return out


def main():
    if not os.path.exists(PATH):
        print('NG: 通り芯のファイルが無い:', PATH); return 1
    try:
        g = json.load(open(PATH, encoding='utf-8'))
    except Exception as e:
        print('NG: 読めない（JSON の書き方が壊れている）:', e); return 1
    X, Y = items(g.get('X') or g.get('x'), 'X'), items(g.get('Y') or g.get('y'), 'Y')
    if not (X and Y) and isinstance(g.get('grids'), list):
        for x in g['grids']:
            ax = str(x.get('axis', x.get('name', '?')))[:1].upper()
            (X if ax == 'X' else Y).extend(items([x], ax))
    if not X or not Y:
        print('NG: X と Y の通り芯が両方そろっていない', {'X': X, 'Y': Y}); return 1
    if max(abs(c) for _, c in X + Y) > 100:
        X = [(n, c / 1000) for n, c in X]; Y = [(n, c / 1000) for n, c in Y]; print('mm と見て m に直した')
    X.sort(key=lambda a: a[1]); Y.sort(key=lambda a: a[1])
    norm = {'unit': 'm', 'X': [{'name': n, 'coord': round(c, 4)} for n, c in X],
            'Y': [{'name': n, 'coord': round(c, 4)} for n, c in Y]}
    for k in ('project', 'note'):
        if k in g: norm[k] = g[k]
    def kit_form(v):   # すでにキットの形（name・coord の dict のリスト。ほかの項目はあってよい）か
        return isinstance(v, list) and all(isinstance(x, dict) and 'name' in x and isinstance(x.get('coord'), (int, float)) for x in v)
    same = kit_form(g.get('X')) and kit_form(g.get('Y')) and max(abs(x['coord']) for x in g['X'] + g['Y']) <= 100
    if not same:
        shutil.copyfile(PATH, os.path.join(os.path.dirname(PATH), 'grid_raw.json'))
        json.dump(norm, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('形をそろえて書き直した（元は grid_raw.json）')
    print('X:', ', '.join(f'{n}={c}' for n, c in X))
    print('Y:', ', '.join(f'{n}={c}' for n, c in Y))
    print(f'OK: 通り芯 X {len(X)} 本・Y {len(Y)} 本')
    return 0


if __name__ == '__main__':
    sys.exit(main())
