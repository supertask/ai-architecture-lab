"""Archicad（JSON API）と Tapir に届くかを確かめる。何も変えない（--save を付けた時だけ保存する）。

使い方：
    python check_connection.py          # 接続の確認だけ
    python check_connection.py --save   # 確認して SaveProject（run_sheets.sh が1枚ごとに使う）
ポートは環境変数 ARCHICAD_PORT（既定 19723）。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))


def main():
    try:
        r = t.api(P, 'API.IsAlive', timeout=10)
    except Exception as e:
        print(f'NG: ポート {P} に Archicad が見つからない（{type(e).__name__}）。Archicad を起動し、プロジェクトを開いてから再実行。')
        return 1
    if not (r.get('succeeded') and r.get('result', {}).get('isAlive')):
        print('NG: Archicad の応答が想定と違う:', r); return 1
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
        print('NG: Tapir の命令が通らない。Tapir アドオンを入れて Archicad を再起動する。', str(e)[:200]); return 1
    try:
        st = t.call(P, 'GetStories', {}, timeout=10)['stories']
        print('   階:', [(s['name'], round(s['level'], 3)) for s in st])
    except Exception as e:
        print('   （階を読めなかった。プロジェクトが開いているか確かめる）', str(e)[:120])
    if '--save' in sys.argv[1:]:
        try:
            print('save', t.call(P, 'SaveProject', {}, timeout=300))
        except Exception as e:
            print('NG: SaveProject に失敗（無題のプロジェクトは一度 GUI で名前を付けて保存する）', str(e)[:200]); return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
