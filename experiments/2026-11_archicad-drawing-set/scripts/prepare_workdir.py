"""作業フォルダを作る：指示（prompts/）が読むファイルを1か所に集め、指示文の <KIT>・<KITROOT>・ポートを実際の値に置き換える。

使い方：
    python scripts/prepare_workdir.py                 # キット直下に work/ を作る
    python scripts/prepare_workdir.py D:/ac-work      # 置き場所を指定
    python scripts/prepare_workdir.py --with-grid     # 通り芯 grid.json も入れる（02 の回を飛ばす時だけ）

作るもの（<WORK> = 作業フォルダ）：
    <WORK>/tapir_http.py, <WORK>/作図ルール_*.md, <WORK>/rhino_house.py,
    <WORK>/rhino_house.png, <WORK>/layout_1F.png, <WORK>/layout_2F.png（公開版の .jpg を .png に変換）,
    <WORK>/prompts/*.md（<KIT>/ を <WORK>/ に、<KITROOT>/ をキットの場所に、「port は 19723」を使うポートに置き換えた版）,
    <WORK>/skills/*.md（操作のコツ・点検の手順）, <WORK>/progress.md（無ければ作る。進み具合の記録）
何度流してもよい（指示とルールを元から作り直す。grid.json・progress.md・保存した .pln は消さない）。
元の prompts/ は書き換えない。Archicad には触らない。
"""
import os, sys, shutil, glob

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, 'scripts'))
import tapir_http as t


def to_png(src, dst):
    try:
        from PIL import Image
        Image.open(src).convert('RGB').save(dst)
        return 'png'
    except ImportError:
        # Pillow が無い時は中身 JPEG のまま名前だけ .png にする（多くの画像読み込みは中身で判定するので読める）
        shutil.copyfile(src, dst)
        return 'jpeg-as-png（Pillow を入れると本物の PNG にできる）'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    work = os.path.abspath(args[0] if args else os.path.join(KIT, 'work')).replace('\\', '/')
    kit = KIT.replace('\\', '/')
    port = t.default_port()
    os.makedirs(os.path.join(work, 'prompts'), exist_ok=True)
    shutil.copyfile(os.path.join(KIT, 'scripts', 'tapir_http.py'), os.path.join(work, 'tapir_http.py'))
    pf = os.path.join(KIT, 'work', 'archicad_port.txt')
    if os.path.exists(pf) and os.path.abspath(os.path.join(work, 'archicad_port.txt')) != os.path.abspath(pf):
        shutil.copyfile(pf, os.path.join(work, 'archicad_port.txt'))
    for f in glob.glob(os.path.join(KIT, 'rules', '*.md')):
        if os.path.basename(f).startswith('README'):
            continue
        shutil.copyfile(f, os.path.join(work, os.path.basename(f)))
    shutil.copyfile(os.path.join(KIT, 'inputs', 'rhino_house.py'), os.path.join(work, 'rhino_house.py'))
    os.makedirs(os.path.join(work, 'skills'), exist_ok=True)
    for f in glob.glob(os.path.join(KIT, 'skills', '*.md')):
        shutil.copyfile(f, os.path.join(work, 'skills', os.path.basename(f)))
    for name in ('rhino_house', 'layout_1F', 'layout_2F'):
        how = to_png(os.path.join(KIT, 'inputs', name + '.jpg'), os.path.join(work, name + '.png'))
        print(f'{name}.png ({how})')
    if '--with-grid' in sys.argv:
        shutil.copyfile(os.path.join(KIT, 'scripts', 'grid.json'), os.path.join(work, 'grid.json'))
        print('grid.json（実験の記録の通り芯）を入れた')
    n = 0
    for f in sorted(glob.glob(os.path.join(KIT, 'prompts', '*.md'))):
        s = open(f, encoding='utf-8').read()
        s = s.replace('<KITROOT>/', kit + '/').replace('<KITROOT>', kit)
        s = s.replace('<KIT>/', work + '/').replace('<KIT>', work)
        s = s.replace('port は 19723', f'port は {port}')
        open(os.path.join(work, 'prompts', os.path.basename(f)), 'w', encoding='utf-8').write(s)
        n += 1
    prog = os.path.join(work, 'progress.md')
    if not os.path.exists(prog):
        open(prog, 'w', encoding='utf-8').write('# 進み具合（1行ずつ足す：日時・指示の名前・結果・保存したか）\n')
    print(f'prompts {n} 本を {work}/prompts/ に書いた（port {port}）')
    print(f'作業フォルダ: {work}')
    print(f'次：新しい会話で「work/prompts/01_model_M.md を読んで、指示どおりに作業してください」')


if __name__ == '__main__':
    main()
