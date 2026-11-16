"""立面4面（建物の外に置いた断面線）と断面2面（A-A・B-B）を作り、画像に書き出す。

使い方：
    python make_sections.py create                 # 断面線を作る（外壁ができてから＝prompts/01 の後）
    （ここで GUI：ナビゲータ › プロジェクト一覧 › 断面図 の6つを、それぞれ1回ダブルクリックして開く）
    python make_sections.py shoot                  # 6面を <KIT>/out/sections/ に PNG で書き出して確かめる
    python make_sections.py create --aa-y 3.0 --bb-x 9.5 --margin 3.0   # 位置を変える時

元：実験の前の回で使った断面作成スクリプト（この家の元のモデルで作り、その断面ビューを残したまま
「白紙」のプロジェクトに作り直した）。ここではパスとポートだけ一般化した。
- 立面は、建物の外 margin m に置いた断面線で作る（テンプレートの立面マーカーは空のプロジェクト用の位置で、中身が空になった）。
  名前：S南・S東・S北・S西。断面：A-A（y=一定で東西に切る）、B-B（x=一定で南北に切る）。
- 断面線は「始点→終点の左側」を見る。
- 既定値はこの家用（A-A は y=3.0：水盤・吹抜け・階段を通る。B-B は x=9.5：LDK・寝室を通る）。
- 注意：create は、プロジェクトの断面マーカー（CutPlane 要素）を全部消してから作る（再実行のため）。
  ほかの断面があるプロジェクトでは使わない。
- 窓の表示名は「参照ID 名前」（既定の参照ID は S-01 なので「S-01 A-A」）。指示文はこの表示名で窓を探す。
  平面に出る断面記号の参照ID を A / B に変えるのは GUI だけ（断面図を右クリック →「断面図の名前を変更...」）。
- 版によっては、作ったばかりの断面の窓を API で開けない（ChangeWindow が "Failed to change current database"）。
  ナビゲータで1回ダブルクリックして開くと、以後は databaseId で切り替えられる。
"""
import os, sys, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
OUT = os.path.join(os.path.dirname(HERE), 'out', 'sections')
FILE = {'S南': '01_south', 'S東': '02_east', 'S北': '03_north', 'S西': '04_west', 'A-A': '05_section_AA', 'B-B': '06_section_BB'}


def call(c, p): return t.call(P, c, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['create', 'shoot'])
    ap.add_argument('--aa-y', type=float, default=3.0)
    ap.add_argument('--bb-x', type=float, default=9.5)
    ap.add_argument('--margin', type=float, default=3.0)
    a = ap.parse_args()

    call('ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
    # 建物の範囲（壁の端点から。地面スラブは大きいので使わない）
    ws = call('GetElementsByType', {'elementType': 'Wall'})['elements']
    if not ws: sys.exit('壁がない。外壁を作ってから（prompts/01 の後に）流す。')
    xs, ys = [], []
    for d in call('GetDetailsOfElements', {'elements': ws})['detailsOfElements']:
        x = d['details']
        for k in ('begCoordinate', 'endCoordinate'):
            if k in x: xs.append(x[k]['x']); ys.append(x[k]['y'])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    print('bbox', round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))
    M = a.margin
    dx, dy = x1 - x0 + 2 * M, y1 - y0 + 2 * M
    SEC = [
        ('S南', (x0 - M, y0 - M), (x1 + M, y0 - M), dy),
        ('S東', (x1 + M, y0 - M), (x1 + M, y1 + M), dx),
        ('S北', (x1 + M, y1 + M), (x0 - M, y1 + M), dy),
        ('S西', (x0 - M, y1 + M), (x0 - M, y0 - M), dx),
        ('A-A', (x0 - M, a.aa_y), (x1 + M, a.aa_y), dy / 2),   # 東西に切って北を見る
        ('B-B', (a.bb_x, y0 - M), (a.bb_x, y1 + M), dx / 2),   # 南北に切って西を見る
    ]
    if a.step == 'create':
        old = call('GetElementsByType', {'elementType': 'CutPlane'})['elements']
        if old: call('DeleteElements', {'elements': old}); print('deleted old section markers', len(old))
        data = [{'startCoordinate': {'x': p[0], 'y': p[1]}, 'endCoordinate': {'x': q[0], 'y': q[1]}, 'depth': dep, 'name': nm}
                for nm, p, q, dep in SEC]
        print(call('CreateSections', {'sectionsData': data}))
        print('次：ナビゲータの断面図6つを GUI で1回ずつ開く → SaveProject → shoot で確かめる')
        return
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for nm, *_ in SEC:
        dbs = [d for d in call('GetDatabases', {})['databases'] if d.get('type') == 'Section' and d.get('name') == nm]
        if not dbs: print(nm, 'が見つからない'); continue
        try:
            call('ChangeWindow', {'windowType': 'Section', 'databaseId': dbs[0]['databaseId']})
        except Exception as e:
            print(nm, '開けない。ナビゲータで1回ダブルクリックしてから再実行:', str(e)[:120]); continue
        try: call('RebuildView', {})
        except Exception as e: print('rebuild', str(e)[:120])
        call('FitInWindow', {})
        r = call('SaveCurrentWindowAsImage', {'imageFilePath': os.path.join(OUT, FILE[nm] + '.png').replace('\\', '/')})
        out[nm] = r['zoom']; print(nm, r['zoom'])
    call('ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0})
    json.dump(out, open(os.path.join(OUT, 'zoom.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
