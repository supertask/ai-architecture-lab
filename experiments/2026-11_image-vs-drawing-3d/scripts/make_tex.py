from PIL import Image, ImageEnhance
import shutil, os
# 比較用の見せ方の調整（元の PBR 一式は触らず、tex/ に調整した複製を作る）。
# 元：work/materials/<key>/（materials.json で seam → deepbump → make_pbr を通した出力）
# uv run -q --with pillow python scripts/make_tex.py（このフォルダの直下で実行）
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
def cp(src,dst,dark=None,flat_normal=False,skip=()):
    os.makedirs(dst,exist_ok=True)
    for f in ('basecolor','normal','roughness','ao','metallic'):
        p=src+f+'.png'
        if not os.path.exists(p) or f in skip: continue
        if f=='basecolor' and dark:
            im=Image.open(p).convert('RGB'); im=ImageEnhance.Brightness(im).enhance(dark[0]); im=ImageEnhance.Contrast(im).enhance(dark[1]); im.save(dst+f+'.png')
        elif f=='normal' and flat_normal:
            im=Image.open(p).convert('RGB'); flat=Image.new('RGB',im.size,(128,128,255)); Image.blend(im,flat,0.75).save(dst+f+'.png')
        else: shutil.copy(p,dst+f+'.png')
M = B + 'work/materials/'
cp(M+'concrete/',B+'tex/concrete/',dark=(0.72,1.25))
cp(M+'black_mortar/',B+'tex/black_mortar/',flat_normal=True)
cp(M+'rammed_earth/',B+'tex/rammed_earth/')
cp(M+'wood/',B+'tex/wood/')
print(os.listdir(B+'tex'))
# rammed_earth: 彩度0.55・明るさ0.85（make_tex.py の後に適用、2026-11-04）
