"""作業フォルダを作る：指示（prompts/）が読むファイルを1か所に集め、指示文の <KIT> をその場所に置き換える。

使い方：
    python scripts/prepare_workdir.py                 # キット直下に work/ を作る
    python scripts/prepare_workdir.py D:/ac-work      # 置き場所を指定
    python scripts/prepare_workdir.py --with-grid     # 通り芯 grid.json も入れる（02 の回を飛ばす時だけ）

作るもの（<WORK> = 作業フォルダ）：
    <WORK>/tapir_http.py, <WORK>/作図ルール_*.md, <WORK>/rhino_house.py,
    <WORK>/rhino_house.png, <WORK>/layout_1F.png, <WORK>/layout_2F.png（公開版の .jpg を .png に変換）,
    <WORK>/prompts/*.md（<KIT>/ を <WORK>/ に置き換えた版）, <WORK>/skills/*.md（操作のコツ・点検の手順）
元の prompts/ は書き換えない。Archicad には触らない。
"""
import os, sys, shutil, glob

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    os.makedirs(os.path.join(work, 'prompts'), exist_ok=True)
    shutil.copyfile(os.path.join(KIT, 'scripts', 'tapir_http.py'), os.path.join(work, 'tapir_http.py'))
    for f in glob.glob(os.path.join(KIT, 'rules', '*.md')):
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
        s = open(f, encoding='utf-8').read().replace('<KIT>/', work + '/').replace('<KIT>', work)
        open(os.path.join(work, 'prompts', os.path.basename(f)), 'w', encoding='utf-8').write(s)
        n += 1
    print(f'prompts {n} 本を {work}/prompts/ に書いた')
    print(f'作業フォルダ: {work}')
    print(f'次：AI エージェントを {work} で起動し、「{work}/prompts/01_model_M.md を読んで、そのとおりに作業して」と入力')


if __name__ == '__main__':
    main()
