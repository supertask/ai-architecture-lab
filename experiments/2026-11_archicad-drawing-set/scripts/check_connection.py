"""Archicad（JSON API）と Tapir に届くかを確かめる。モデルは変えない（--save を付けた時だけ保存する）。

使い方：
    python check_connection.py          # 接続の確認だけ
    python check_connection.py --scan   # 既定のポートで見つからなければ 19723〜19744 を探し、見つかった番号を
                                        # <KIT>/work/archicad_port.txt に書く（以後のスクリプトはこの番号を使う）
    python check_connection.py --count  # 平面図（1階）に切り替えて、壁・スラブ・ゾーン・2D の数を数える（白紙か確かめる）
    python check_connection.py --save   # 確認して SaveProject（1手順ごとに使う）
ポート：環境変数 ARCHICAD_PORT → work/archicad_port.txt → 19723（tapir_http.default_port）。
終了コード：0＝OK、1＝つながらない、2＝Tapir が無い、3＝保存に失敗。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

KIT = os.path.dirname(HERE)


def alive(p):
    try:
        r = t.api(p, 'API.IsAlive', timeout=5)
        return bool(r.get('succeeded') and r.get('result', {}).get('isAlive'))
    except Exception:
        return False


def main():
    args = sys.argv[1:]
    P = t.default_port()
    if not alive(P):
        found = None
        if '--scan' in args:
            for p in range(19723, 19745):
                if p != P and alive(p):
                    found = p; break
        if found is None:
            print(f'NG: ポート {P} に Archicad が見つからない。Archicad を起動し、プロジェクトを開いてから再実行。'
                  '（Archicad を2つ以上開いている時は --scan で探せる）')
            return 1
        P = found
        os.makedirs(os.path.join(KIT, 'work'), exist_ok=True)
        open(os.path.join(KIT, 'work', 'archicad_port.txt'), 'w', encoding='utf-8').write(str(P))
        print(f'ポート {P} で見つけた → work/archicad_port.txt に書いた')
    print(f'OK: Archicad JSON API（port {P}）')
    try:
        info = t.api(P, 'API.GetProductInfo', timeout=10).get('result', {})
        print('   製品情報:', {k: info.get(k) for k in ('version', 'buildNumber', 'languageCode')})
    except Exception:
        pass
    try:
        v = t.call(P, 'GetAddOnVersion', {}, timeout=10)
        print('OK: Tapir アドオン', v.get('version', v))
    except Exception as e:
        print('NG: Tapir の命令が通らない。Tapir アドオンを入れて Archicad を再起動する。', str(e)[:200]); return 2
    try:
        st = t.call(P, 'GetStories', {}, timeout=10)['stories']
        print('   階:', [(s['name'], round(s['level'], 3)) for s in st])
    except Exception as e:
        print('   （階を読めなかった。プロジェクトが開いているか確かめる）', str(e)[:120])
    if '--count' in args:
        # 3D の窓のままだと要素が 0 で返るので、平面図（1階）に切り替えてから数える
        try:
            t.call(P, 'ChangeWindow', {'windowType': 'FloorPlan', 'storyIndex': 0}, timeout=30)
        except Exception as e:
            print('   （平面図に切り替えられなかった）', str(e)[:120])
        counts = {}
        for ty in ('Wall', 'Slab', 'Window', 'Door', 'Zone', 'Stair', 'Line', 'Text', 'Dimension', 'Hatch'):
            try:
                counts[ty] = len(t.call(P, 'GetElementsByType', {'elementType': ty}, timeout=60)['elements'])
            except Exception:
                counts[ty] = '?'
        print('   要素の数:', counts)
        print('   白紙:', 'はい' if all(v == 0 for v in counts.values() if v != '?') else 'いいえ（すでに要素がある）')
    if '--save' in args:
        try:
            print('save', t.call(P, 'SaveProject', {}, timeout=300))
        except Exception as e:
            print('NG: SaveProject に失敗（無題のプロジェクトは一度 GUI で名前を付けて保存する。Archicad が落ちた可能性もある）', str(e)[:200]); return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
