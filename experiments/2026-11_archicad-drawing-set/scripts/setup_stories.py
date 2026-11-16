"""空のプロジェクトの階を 1FL・2FL・RFL の3つにする（実験の開始状態）。必要なら名前を付けて保存する。

使い方：
    python setup_stories.py                                   # 階だけ
    python setup_stories.py C:/path/to/kit/work/house_from_scratch.pln   # 階を設定して、その名前で保存

元：実験の前の回の組み立てスクリプトの stories()（階の設定部分）を取り出したもの。
- 高さは この家の値（1FL=0、2FL=3.15、RFL=6.8。単位 m）。モデルを直す回（fixA_raise.py）で全部 +0.1 上がる。
- dispOnSections=False：立面・断面に Archicad の階の印（▽2FL など）を出さない。作図ルールではレベルを 2D で描くため。
- index は先頭だけに付ける（全部に付けると失敗した）。Tapir の版によっては、2回目以降の SetStories が
  「Failed to change story height」で失敗する。最初に1回だけ流す。
- 保存先を渡すと SaveProject {projectPath} を送る。無題のプロジェクトはこれで .pln になる。
  名前の付いたプロジェクトでは「別名で保存」になり、開いているファイルが切り替わるので注意。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tapir_http as t

P = int(os.environ.get('ARCHICAD_PORT', '19723'))
STORIES = [
    {'index': 0, 'name': '1FL', 'level': 0.0, 'dispOnSections': False},
    {'name': '2FL', 'level': 3.15, 'dispOnSections': False},
    {'name': 'RFL', 'level': 6.8, 'dispOnSections': False},
]

if __name__ == '__main__':
    print(t.call(P, 'SetStories', {'stories': STORIES}))
    print([(s['index'], s['name'], s['level'], s['dispOnSections']) for s in t.call(P, 'GetStories', {})['stories']])
    if len(sys.argv) > 1:
        path = os.path.abspath(sys.argv[1])
        print(t.call(P, 'SaveProject', {'projectPath': path}))
        print('保存したか、ファイルの更新時刻で確かめる:', path, os.path.exists(path))
