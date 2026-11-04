from PIL import Image, ImageEnhance
import shutil, os
B='C:/path/to/kit/'
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
cp(B+'model_v12/materials/concrete/','tex/concrete/',dark=(0.72,1.25))
cp(B+'texture_patterns/m/08_black_mortar/','tex/black_mortar/',flat_normal=True)
cp(B+'texture_patterns/m/06_rammed_earth/','tex/rammed_earth/')
print(os.listdir('tex'))
# rammed_earth: 彩度0.55・明るさ0.85（make_tex.py の後に適用、2026-11-04）
