# 形の比較：正解（C_reference_v14）と A・B のシルエットを平面・正面・右側面・裏で重ねて、重なり率（IoU）を出す
# uv run -q --with pillow --with numpy python scripts/metrics_live.py [work/compare のパス]
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fontutil import font
# 入力：run_compare.py が書いた work/compare/<名前>/sil_*.png（引数で別の場所も可。Rhino 無しで数字だけ確かめるなら results/silhouettes を渡す）　出力：run2_recorded/results/
# 引数：[影絵のフォルダ] [--out 書き出し先] [--tags A_image_only,B_image_plus_drawing]（--out を付けると公開済みの結果を上書きしない）
ARGS = sys.argv[1:]
def _opt(k):
    if k in ARGS:
        i = ARGS.index(k); v = ARGS[i + 1]; del ARGS[i:i + 2]; return v
OUT_OPT, TAGS_OPT = _opt('--out'), _opt('--tags')
D = (ARGS[0] if ARGS else os.path.join(HERE, '..', 'work', 'compare')) + '/'
RES = os.path.join(HERE, '..', 'run2_recorded', 'results') + '/'
if OUT_OPT: RES = os.path.abspath(OUT_OPT) + '/'
os.makedirs(RES, exist_ok=True)
REF = 'C_reference_v14'
TAGS = [('A_image_only', '外観だけ（1回目）'), ('B_image_plus_drawing', '外観＋図面（1回目）'), ('live_A', '外観だけ（録画回）'), ('live_B', '外観＋図面（録画回）')]
if TAGS_OPT: TAGS = [t for t in TAGS if t[0] in TAGS_OPT.split(',')]
VIEWS = [('top', '真上（平面）'), ('front', '正面'), ('right', '右側面'), ('back', '裏')]
F = font

def mask(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(int)
    bg = np.median(np.concatenate([a[:5].reshape(-1, 3), a[-5:].reshape(-1, 3), a[:, :5].reshape(-1, 3), a[:, -5:].reshape(-1, 3)]), axis=0)
    return np.abs(a - bg).sum(axis=2) > 30

def edge(m):
    e = np.zeros_like(m)
    e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:])
    return e

res = {}
rows = []
for tag, jp in TAGS:
    if not os.path.exists(D + tag + '/sil_top.png'):
        continue
    res[tag] = {}
    row = []
    for v, vj in VIEWS:
        r = mask(D + REF + '/sil_%s.png' % v); m0 = mask(D + tag + '/sil_%s.png' % v)
        # 原点の決め方の差を消すため、±60px（約±3m）の平行移動で一番重なる位置に合わせる（A・B 同じ条件）
        best = (-1, 0, 0)
        for dy in range(-60, 61, 3):
            for dx in range(-60, 61, 3):
                mm = np.roll(np.roll(m0, dy, 0), dx, 1); sc = (r & mm).sum() / max(1, (r | mm).sum())
                if sc > best[0]: best = (sc, dx, dy)
        m = np.roll(np.roll(m0, best[2], 0), best[1], 1)
        iou = (r & m).sum() / max(1, (r | m).sum())
        miss = (r & ~m).sum() / max(1, r.sum()); extra = (m & ~r).sum() / max(1, r.sum())
        res[tag][v] = dict(iou=round(float(iou), 3), missing=round(float(miss), 3), extra=round(float(extra), 3))
        # 重ね図：灰＝両方、赤＝正解にあるのに無い、青＝正解に無いのにある
        img = np.full(r.shape + (3,), 255, np.uint8)
        img[r & m] = (200, 200, 200); img[r & ~m] = (230, 60, 60); img[m & ~r] = (60, 120, 230)
        e = edge(r); img[e] = (40, 40, 40)
        im = Image.fromarray(img)
        ys, xs = np.where(r | m)
        if len(xs):
            pad = 40; im = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad), min(im.height, ys.max() + pad)))
        im.thumbnail((620, 420)); c = Image.new('RGB', (640, 480), 'white'); c.paste(im, (10, 50))
        dr = ImageDraw.Draw(c); dr.text((10, 8), '%s｜%s　重なり %d%%' % (jp, vj, round(iou * 100)), fill='black', font=F(22))
        row.append(c)
    rows.append(row)
if not res:
    raise SystemExit('work/compare/<名前>/sil_top.png が見つからない。先に Rhino で scripts/run_all_in_rhino.py を実行する')
json.dump(res, open(RES + 'metrics_live.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if rows:
    S = Image.new('RGB', (640 * 4, 480 * len(rows) + 60), 'white'); dr = ImageDraw.Draw(S)
    dr.text((12, 14), '形の重なり（正解＝図面どおりに直してきた模型 v14）　灰＝一致　赤＝足りない　青＝余分', fill='black', font=F(26))
    for i, row in enumerate(rows):
        for j, c in enumerate(row): S.paste(c, (640 * j, 60 + 480 * i))
    S.save(RES + 'overlap_sheet_live.png')
print(json.dumps(res, ensure_ascii=False))
