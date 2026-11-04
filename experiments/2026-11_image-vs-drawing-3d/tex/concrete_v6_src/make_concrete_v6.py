# 外観 v6 の打放しに寄せた、リピート感の出ない大判テクスチャを組む
#  - 地のコンクリートは Qwen-Image 2.1（v6 外観を入力にした edit）で作った「Pコン・目地なし」の素地 3〜5 枚
#  - 14.4m x 14.4m（型枠 900x1800 を 横16 x 縦8 枚）を 1 枚のタイルにする。各パネルに素地のランダムな切り抜き・反転・明るさ差
#  - 目地とPコン（1 パネル 2x3、横 450・縦 600 ピッチ）はプログラムで正確に描く（AI が描くと間隔がばらつくため）
#  - 大きなむら（数 m 単位、タイル全体で継ぎ目なし）を掛けて、同じ模様の繰り返しを目立たなくする
#  - 出力：basecolor / height / normal / roughness / ao / metallic（tex/concrete_v6/）
# uv run -q --with pillow --with numpy python make_concrete_v6.py
import os, glob, math, random
import numpy as np
from PIL import Image, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = D + '../tex/concrete_v6/'
os.makedirs(OUT, exist_ok=True)
random.seed(7); rng = np.random.default_rng(7)
TILE_MM, PX = 14400, 4096   # 14.4m 角：家の幅（約17m）でほぼ1回しか繰り返さない
S = PX / TILE_MM                      # px / mm
PW, PH = 900, 1800                    # 型枠パネル
def despeckle(p):
    # AI が消しきれなかった Pコンの名残（周りより暗い小さな点）を、周りの中央値で埋める
    im = Image.open(p).convert('RGB')
    a = np.asarray(im).astype(np.float32); med = np.asarray(im.filter(ImageFilter.MedianFilter(15))).astype(np.float32)
    m = (med.mean(2) - a.mean(2)) > 14
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    a[m] = med[m]
    return a
srcs = [despeckle(p) for p in sorted(glob.glob(D + 'plain_*.png'))]
assert srcs, 'plain_*.png が無い'
# 素地の明るさ・色をそろえる（全体の平均に合わせる）。目標色は v6 の壁（明るいニュートラルグレー）
TARGET = np.array([138, 137, 138], np.float32)   # v6C の壁の実測（無彩色の画素の中央値 163,161,161）に、Rhino レンダー後の値が合うよう調整
# AI の素地からは「細かい質感（気泡・砂目）」だけを使う。大きな染みはパネルの縁で切れて継ぎはぎに見えるので、
# ぼかした成分を引いて取り除き、大きなむらは下の FFT ノイズ（パネルをまたいで連続、継ぎ目なし）で付ける
def highpass(a, r=20):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return a - np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
srcs = [highpass(s) for s in srcs]
srcs = [h * (4.0 / (h.mean(2).std() + 1e-3)) + TARGET for h in srcs]
img = np.zeros((PX, PX, 3), np.float32)
pw, ph = int(round(PW * S)), int(round(PH * S))
for j in range(TILE_MM // PH):
    for i in range(TILE_MM // PW):
        s = srcs[random.randrange(len(srcs))]
        # 素地 1 枚 = 1.8m 角として拡大し、パネル大の切り抜きを取る
        k = (1800 * S) / s.shape[0] * random.uniform(1.0, 1.6)   # 拡大率を毎回変えて、同じ模様が並ばないように
        sh, sw = int(s.shape[0] * k), int(s.shape[1] * k)
        big = np.asarray(Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)).resize((sw, sh), Image.BICUBIC)).astype(np.float32)
        if random.random() < 0.5: big = big[:, ::-1]
        if random.random() < 0.5: big = big[::-1]
        y0 = random.randrange(0, max(1, sh - ph)); x0 = random.randrange(0, max(1, sw - pw))
        cut = big[y0:y0 + ph, x0:x0 + pw]
        if cut.shape[0] < ph or cut.shape[1] < pw:
            cut = np.asarray(Image.fromarray(np.clip(cut, 0, 255).astype(np.uint8)).resize((pw, ph))).astype(np.float32)
        cut = cut * (1 + rng.normal(0, 0.006))   # パネルごとの打ち色の差（ごく弱く。強いと市松に見える）
        Y, X = j * ph, i * pw
        img[Y:Y + ph, X:X + pw] = cut[:min(ph, PX - Y), :min(pw, PX - X)]
# むら：FFT の低域ノイズ（周期＝タイル幅なので継ぎ目なし、帯や波の向きが出ない）。弱め
def fnoise(cut, seed):
    r = np.random.default_rng(seed); w = r.standard_normal((PX, PX)).astype(np.float32)
    fy = np.fft.fftfreq(PX)[:, None]; fx = np.fft.fftfreq(PX)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2); F = np.fft.fft2(w) * np.exp(-(f / cut) ** 2)
    n = np.real(np.fft.ifft2(F)); return (n / np.abs(n).max()).astype(np.float32)
macro = 0.6 * fnoise(0.004, 11) + 0.4 * fnoise(0.015, 12)
img *= (1 + 0.07 * macro)[..., None]   # v6 の雲状の大きなむら
# 縦の淡い流れ（雨筋）：ランダムな位置に、上から薄く
streak = np.zeros((PX, PX), np.float32)
for _ in range(30):
    x = rng.integers(0, PX); w = rng.integers(3, 12); L = rng.integers(PX // 10, PX // 3); y = rng.integers(0, PX)
    seg = np.linspace(1, 0, L)
    for t in range(L):
        streak[(y + t) % PX, x:x + w] += seg[t]
streak = np.asarray(Image.fromarray((np.clip(streak, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
img *= (1 - 0.03 * streak)[..., None]
# 目地とPコン（高さマップにも入れる）
height = np.full((PX, PX), 0.5, np.float32)
dark = np.zeros((PX, PX), np.float32)
for X in range(0, PX, pw):
    dark[:, X:X + 2] = 0.35; height[:, X:X + 2] = 0.42
for Y in range(0, PX, ph):
    dark[Y:Y + 2, :] = 0.35; height[Y:Y + 2, :] = 0.42
r = max(5, int(12.5 * S))           # Pコン 25mm
cy, cx = np.mgrid[-r - 3:r + 4, -r - 3:r + 4]; dist = np.sqrt(cx ** 2 + cy ** 2)
disc = np.clip(r + 0.5 - dist, 0, 1); ring = np.clip(1 - np.abs(dist - r) / 1.5, 0, 1)
for Y0 in range(0, PX, ph):
    for X0 in range(0, PX, pw):
        for a in (225, 675):
            for b in (300, 900, 1500):
                x = X0 + int(round(a * S)) + int(rng.integers(-1, 2)); y = Y0 + int(round(b * S)) + int(rng.integers(-1, 2))
                ys, xs = slice(y - r - 3, y + r + 4), slice(x - r - 3, x + r + 4)
                if y - r - 3 < 0 or x - r - 3 < 0 or y + r + 4 > PX or x + r + 4 > PX: continue
                dark[ys, xs] = np.maximum(dark[ys, xs], 1.4 * disc - 0.25 * np.clip(ring - disc, 0, 1))
                height[ys, xs] = np.minimum(height[ys, xs], 0.5 - 0.2 * disc)
img *= (1 - 0.15 * dark)[..., None]   # Pコン・目地は控えめ（v6 では小さく薄い）
base = np.clip(img, 0, 255).astype(np.uint8)
Image.fromarray(base).save(OUT + 'basecolor.png')
# 高さ：細かい凹凸は色の明るさの高周波から少しだけ
lum = base.mean(2).astype(np.float32) / 255
blur = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
height = np.clip(height + 0.25 * (lum - blur), 0, 1)
Image.fromarray((height * 255).astype(np.uint8)).save(OUT + 'height.png')
# 法線（タイルの端で継ぎ目が出ないよう roll で差分）
st = 6.0
dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * st; dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * st
n = np.dstack([-dx, dy, np.ones_like(dx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(OUT + 'normal.png')
rough = np.clip(0.82 + 0.06 * macro - 0.1 * dark + 0.03 * rng.standard_normal((PX, PX)).astype(np.float32), 0, 1)
Image.fromarray((rough * 255).astype(np.uint8)).save(OUT + 'roughness.png')
ao = np.clip(1 - 0.6 * (0.5 - np.asarray(Image.fromarray((height * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255).clip(0), 0, 1)
Image.fromarray((ao * 255).astype(np.uint8)).save(OUT + 'ao.png')
Image.fromarray(np.zeros((64, 64), np.uint8)).save(OUT + 'metallic.png')
# 確認用：タイルを 2x2 並べた縮小（リピート感の確認）
prev = Image.fromarray(base).resize((1024, 1024))
P = Image.new('RGB', (2048, 2048))
for a in (0, 1024):
    for b in (0, 1024): P.paste(prev, (a, b))
P.save(D + 'tile_2x2_preview.jpg', quality=88)
print('ok', len(srcs), 'sources', base.shape)
