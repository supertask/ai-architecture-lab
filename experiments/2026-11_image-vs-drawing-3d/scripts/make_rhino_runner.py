"""あなたの A・B の模型を、正解と同じ条件で撮るための Rhino 用ファイルを作る（Rhino には触らない）。

使い方（キットのフォルダで）：
    python scripts/make_rhino_runner.py                # work/mine/A/model.py・work/mine/B/model.py のある方を撮る
    python scripts/make_rhino_runner.py --only A       # A だけ
できるもの：work/run_mine_here.py（このキットの場所を書き込み済み）。
  - 人が撮る時：Rhino の ScriptEditor（Python）でこのファイルを開いて実行する。
  - AI が Rhino 接続で撮る時：その「Python を実行する」ツールに、このファイルの中身をそのまま送る。
撮影結果：work/compare/C_reference_v14/・A_image_only/・B_image_plus_drawing/（sil_*.png・eye_*.png・model.3dm）。
撮影中は Rhino の窓の大きさを変えない（平行投影の縮尺が変わり、重なり率が崩れる）。
"""
import os, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'


def main():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else 'AB'
    jobs = ["log.append(run(KIT + 'outputs/reference_v14.py', 'C_reference_v14', False, WALLS))"]
    for w, tag, align in (('A', 'A_image_only', True), ('B', 'B_image_plus_drawing', False)):
        p = KIT + 'work/mine/%s/model.py' % w
        if w in only and os.path.exists(p):
            jobs.append("log.append(run(KIT + 'work/mine/%s/model.py', '%s', %s, WALLS))" % (w, tag, align))
        elif w in only:
            print('無い（飛ばす）:', p)
    if len(jobs) == 1:
        sys.exit('work/mine/A/model.py も work/mine/B/model.py も無い。先に模型を作った会話の model.py をコピーする')
    src = ("# -*- coding: utf-8 -*-\n"
           "# make_rhino_runner.py が作ったファイル。Rhino の ScriptEditor で開いて実行する（撮影中は窓の大きさを変えない）。\n"
           "import io\n"
           "KIT = %r\n"
           "g = {'KIT_OVERRIDE': KIT}\n"
           "exec(io.open(KIT + 'scripts/run_compare.py', encoding='utf-8').read(), g)\n"
           "run = g['run']\n"
           "WALLS = ('concrete', 'black_mortar', 'rammed_earth')\n"
           "log = []\n" % KIT) + '\n'.join(jobs) + "\nresult = ' | '.join(log)\nprint(result)\n"
    os.makedirs(KIT + 'work', exist_ok=True)
    open(KIT + 'work/run_mine_here.py', 'w', encoding='utf-8').write(src)
    print('書いた:', KIT + 'work/run_mine_here.py', '（撮る物:', len(jobs), '）')


if __name__ == '__main__':
    main()
