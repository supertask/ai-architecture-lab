"""継ぎ目（タイリング）の確認と修正。

  uv run -q --with numpy --with pillow python scripts/archviz/material/seam.py check <img...> [--sheet out.jpg]
  uv run -q --with numpy --with pillow python scripts/archviz/material/seam.py fix <in.png> <out.png> [--sat 0.7] [--gain 1,1,1] [--band 0.12] [--thresh 1.4]
  uv run -q --with numpy --with pillow python scripts/archviz/material/seam.py config <materials.json> [--only k1,k2]   # raw.png → basecolor_src.png を全素材
継ぎ目比 = 端と端の差の平均 / 隣り合う画素の差の平均（1.0 = 内部と同じ滑らかさ）。1.4 を超える軸だけ、
端の帯（12%）を「模様の周期ぶんずらした自分のコピー」と混ぜる（目地の線が継ぎ目に来ないずらし量を選ぶ）。
GPT Image に「seamless」と頼んでも継ぎ目比 3〜12 の素材が出る（v4: 樹脂杉 3.6/12.6 → 0.7/1.1 に修正）。
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import keys_of, load_config, mat_dir  # noqa: E402


def seam_ratio(a, axis):
    a = a.astype(np.float32)
    inner = np.abs(np.diff(a, axis=axis)).mean()
    edge = np.abs(np.take(a, 0, axis) - np.take(a, -1, axis)).mean()
    return float(edge / (inner + 1e-9))


def ratios(a):
    return round(seam_ratio(a, 1), 2), round(seam_ratio(a, 0), 2)   # (x, y)


def best_shift(profile):
    n = len(profile)
    p = profile - profile.mean()
    cands = sorted(range(n // 4, 3 * n // 4), key=lambda s: -float(np.dot(p, np.roll(p, s))))[:12]
    return min(cands, key=lambda s: profile[(n - s - 1) % n])


def ramp(n, band):
    t = np.arange(n) + 0.5
    w = np.clip(np.minimum(t, n - t) / band, 0, 1)
    return w * w * (3 - 2 * w)


def fix_array(a, band_frac=0.12, thresh=1.4):
    a = a.astype(np.float64)
    info = {}
    lum = a.mean(-1)
    if seam_ratio(a, 1) > thresh:
        w = ramp(a.shape[1], band_frac * a.shape[1])
        sx = best_shift(np.abs(np.diff(lum, axis=1)).mean(0))
        a = a * w[None, :, None] + np.roll(a, sx, 1) * (1 - w[None, :, None])
        info["x_shift"] = int(sx)
        lum = a.mean(-1)
    if seam_ratio(a, 0) > thresh:
        w = ramp(a.shape[0], band_frac * a.shape[0])
        sy = best_shift(np.abs(np.diff(lum, axis=0)).mean(1))
        a = a * w[:, None, None] + np.roll(a, sy, 0) * (1 - w[:, None, None])
        info["y_shift"] = int(sy)
    return a, info


def desat(a, sat=1.0, gain=(1.0, 1.0, 1.0)):
    l = a.mean(-1, keepdims=True)
    return (l + (a - l) * sat) * np.array(gain)[None, None, :]


def fix_file(src, dst, sat=1.0, gain=(1, 1, 1), band=0.12, thresh=1.4):
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
    before = ratios(a)
    if sat != 1.0 or tuple(gain) != (1, 1, 1):
        a = desat(a, sat, gain)
    a, info = fix_array(a, band, thresh)
    after = ratios(a)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).save(dst)
    return {"seam_before_xy": before, "seam_after_xy": after, **info}


def tiled_sheet(paths, out, cell=384, cols=3):
    tiles = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        a = np.asarray(im)
        r = ratios(a)
        t = im.resize((cell, cell), Image.LANCZOS)
        big = Image.new("RGB", (cell * 2, cell * 2))
        for i in range(2):
            for j in range(2):
                big.paste(t, (i * cell, j * cell))
        d = ImageDraw.Draw(big)
        d.rectangle([0, 0, cell * 2, 24], fill=(0, 0, 0))
        d.text((6, 5), "%s  seam x%.2f y%.2f" % (Path(p).parent.name + "/" + Path(p).name, r[0], r[1]), fill=(255, 255, 255))
        tiles.append(big)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cell * 2 * min(cols, len(tiles)), cell * 2 * rows), (20, 20, 20))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * cell * 2, (k // cols) * cell * 2))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("images", nargs="+")
    c.add_argument("--sheet")
    f = sub.add_parser("fix")
    f.add_argument("src")
    f.add_argument("dst")
    f.add_argument("--sat", type=float, default=1.0)
    f.add_argument("--gain", default="1,1,1")
    f.add_argument("--band", type=float, default=0.12)
    f.add_argument("--thresh", type=float, default=1.4)
    g = sub.add_parser("config")
    g.add_argument("config")
    g.add_argument("--only")
    g.add_argument("--sheet", help="2x2 並べたシート（既定 <dir>/seam_sheet.jpg）")
    a = ap.parse_args()
    if a.cmd == "check":
        res = {p: ratios(np.asarray(Image.open(p).convert("RGB"))) for p in a.images}
        print(json.dumps(res, indent=1))
        if a.sheet:
            print(tiled_sheet(a.images, a.sheet))
    elif a.cmd == "fix":
        print(json.dumps(fix_file(a.src, a.dst, a.sat, [float(x) for x in a.gain.split(",")], a.band, a.thresh)))
    else:
        cfg = load_config(a.config)
        log, outs = {}, []
        for k in keys_of(cfg, a.only.split(",") if a.only else None):
            d = mat_dir(cfg, k)
            ph = cfg["materials"][k].get("phys", {})
            log[k] = fix_file(d / "raw.png", d / "basecolor_src.png", ph.get("sat", 1.0), ph.get("gain", [1, 1, 1]))
            outs.append(d / "basecolor_src.png")
        (cfg["dir"] / "seam.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
        print(json.dumps(log, indent=1))
        print(tiled_sheet(outs, a.sheet or cfg["dir"] / "seam_sheet.jpg"))


if __name__ == "__main__":
    main()
