"""色画像 + DeepBump から PBR 一式（色・法線・高さ・粗さ・金属度・AO）と material.json を作る。

  uv run -q --with numpy --with pillow --with scipy python scripts/archviz/material/make_pbr.py <materials.json> [--only k1,k2] [--sheet out.jpg]
入力（<dir>/<key>/）: basecolor_src.png, normal_deepbump.png, height_deepbump.png
出力: basecolor.png, normal.png（OpenGL +Y。UE では flip_green）, height.png（16bit）, roughness.png, metallic.png, ao.png,
      material.json（物性値・実測値）, <dir>/pbr_summary.json, <dir>/pbr_sheet.jpg
すべてのフィルタは wrap（端が回り込む）なのでタイリングが保たれる。

phys（素材ごと、全部省略可）:
  rough 0.5        基準の粗さ（物性値で決める。例: 磨いた石 0.25〜0.35, 打ち放し 0.8, 紙 0.6, 研磨金属 0.2〜0.3）
  rough_lum 0.0    明るさとの連動（+ で明るい所ほど粗い）。AIの粗さは色の明るさをなぞりがち（相関0.8超）なので小さく使う
  rough_detail 0.0 細かい変化の振れ幅（明るさの高周波から）
  metallic 0.0     全体の金属度（鋼板なら 1）
  db_k 0.8         DeepBump 法線の強さ   macro_k 0.0  マスクの段差から作る大きな凹凸の強さ
  ao_k 1.0         AO の強さ（平らな板は 0.25 程度）
  masks [ {name, fill(穴の中も埋める), lum:[lo,hi], chroma:[lo,hi], warm:[lo,hi], local:[lo,hi], blur:1.0,
           rough, metallic, height, tint:[r,g,b], tint_mix} ]
     色の条件で部分を選び、その部分だけ粗さ・金属度・高さ・色を変える（例: 真鍮の粒＝明るく暖色で周りより明るい所）
     warm = R−B、chroma = max−min、local = 明るさ − 周囲(半径6px)の明るさ
  sat / gain       seam.py config の色補正（彩度・RGB倍率）
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import keys_of, load_config, load_gray, load_rgb, mat_dir, save8, save16  # noqa: E402

W = "wrap"


def blur(a, s):
    return ndi.gaussian_filter(a, s, mode=W)


def norm01(a):
    lo, hi = np.percentile(a, 0.5), np.percentile(a, 99.5)
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)


def slopes(h):
    return (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5, (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    return round(float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9)), 2)


def mask_from(spec, c):
    lum = c.mean(-1)
    ch = {"lum": lum, "chroma": c.max(-1) - c.min(-1), "warm": c[..., 0] - c[..., 2], "local": lum - blur(lum, 6),
          "green": c[..., 1] - (c[..., 0] + c[..., 2]) / 2}
    m = np.ones_like(lum, dtype=bool)
    for k, v in ch.items():
        if k in spec:
            lo, hi = spec[k]
            m &= (v >= lo) & (v <= hi)
    return np.clip(blur(m.astype(np.float64), spec.get("blur", 1.0)), 0, 1)


def build(d, P):
    c = load_rgb(d / "basecolor_src.png")
    n = c.shape[0]
    lum = c.mean(-1)
    base = c.copy()
    rough = np.full_like(lum, P.get("rough", 0.5))
    metal = np.full_like(lum, P.get("metallic", 0.0))
    macro = np.zeros_like(lum)
    fracs = {}
    if P.get("rough_lum"):
        rough += P["rough_lum"] * (norm01(lum) - 0.5)
    if P.get("rough_detail"):
        rough += P["rough_detail"] * (norm01(lum - blur(lum, 3)) - 0.5) * 2
    for ms in P.get("masks", []):
        m = mask_from(ms, c)
        if ms.get("fill"):   # 輪だけ拾った穴（Pコン等）の中も埋めて凹みにする
            m = np.maximum(m, ndi.binary_fill_holes(m > 0.5).astype(m.dtype))
        fracs[ms.get("name", "mask")] = round(float(m.mean()), 4)
        if "rough" in ms:
            rough = rough * (1 - m) + ms["rough"] * m
        if "metallic" in ms:
            metal = metal * (1 - m) + ms["metallic"] * m
        if "height" in ms:
            macro += ms["height"] * blur(m, ms.get("height_blur", 1.5))
        if "tint" in ms:
            t = np.array(ms["tint"])[None, None, :]
            k = ms.get("tint_mix", 0.6)
            base = base * (1 - m[..., None]) + ((k * t + (1 - k) * c) * m[..., None])
    # 高さ: DeepBump の高さは低周波のうねりが強いので高域だけ使い、マスクの段差（macro）を足す
    hdb = load_gray(d / "height_deepbump.png", n)
    detail = hdb - blur(hdb, n / 40)
    detail = detail / (detail.std() + 1e-9)
    has_macro = np.ptp(macro) > 1e-6
    height = norm01(0.35 * norm01(detail) + 0.65 * norm01(macro)) if has_macro else norm01(detail)
    # 法線: DeepBump × db_k ＋ macro の傾き × macro_k。平均の傾きを0に（タイルする壁に全体の傾きは無い）
    ndb = load_rgb(d / "normal_deepbump.png", n) * 2 - 1
    mx, my = slopes(norm01(macro)) if has_macro else (np.zeros_like(lum), np.zeros_like(lum))
    k = P.get("macro_k", 0.0)
    nx = ndb[..., 0] * P.get("db_k", 0.8) - mx * k
    ny = ndb[..., 1] * P.get("db_k", 0.8) + my * k   # OpenGL: +Y 上、画像の y は下向き
    nz = np.maximum(ndb[..., 2], 0.2)
    nx -= nx.mean()
    ny -= ny.mean()
    v = np.stack([nx, ny, nz], -1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    # AO: 高さの凹み（2スケール）
    cav = np.clip(blur(height, 3) - height, 0, None) * 2.5 + np.clip(blur(height, 14) - height, 0, None) * 1.5
    ao = 1 - (1 - np.clip(1 - cav, 0.55, 1.0)) * P.get("ao_k", 1.0)
    rough = np.clip(rough, 0.02, 1.0)
    metal = np.clip(metal, 0, 1)
    save8(base, d / "basecolor.png")
    save8((v + 1) / 2, d / "normal.png")
    save16(height, d / "height.png")
    save8(ao, d / "ao.png")
    save8(rough, d / "roughness.png")
    save8(metal, d / "metallic.png")
    tilt = np.degrees(np.arccos(np.clip(v[..., 2], -1, 1)))
    mean = v.reshape(-1, 3).mean(0)
    stats = {"mask_fraction": fracs,
             "normal_mean_tilt_deg": round(float(np.degrees(np.arccos(np.clip(mean[2] / np.linalg.norm(mean), -1, 1)))), 2),
             "normal_pct_over20": round(float((tilt > 20).mean() * 100), 1),
             "roughness_mean": round(float(rough.mean()), 3),
             "roughness_range": [round(float(np.percentile(rough, 2)), 2), round(float(np.percentile(rough, 98)), 2)],
             "rough_vs_color_corr": corr(rough, lum),
             "metallic_mean": round(float(metal.mean()), 3), "ao_mean": round(float(ao.mean()), 3)}
    tiles = [base, (v + 1) / 2, height, rough, metal, ao]
    return stats, tiles


def sheet(rows, out):
    heads = ["basecolor", "normal", "height", "roughness", "metallic", "AO"]
    s = Image.new("RGB", (150 + 6 * 260, 28 + len(rows) * 260), "white")
    dr = ImageDraw.Draw(s)
    for j, h in enumerate(heads):
        dr.text((150 + j * 260 + 6, 8), h, fill="black")
    for i, (m, ims) in enumerate(rows):
        dr.text((6, 28 + i * 260 + 120), m, fill="black")
        for j, t in enumerate(ims):
            t = np.repeat(t[..., None], 3, -1) if t.ndim == 2 else t
            s.paste(Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS), (150 + j * 260, 28 + i * 260))
    s.save(out, quality=86)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--only")
    ap.add_argument("--sheet")
    a = ap.parse_args()
    cfg = load_config(a.config)
    summary, rows = {}, []
    for k in keys_of(cfg, a.only.split(",") if a.only else None):
        d = mat_dir(cfg, k)
        m = cfg["materials"][k]
        P = m.get("phys", {})
        stats, tiles = build(d, P)
        (d / "material.json").write_text(json.dumps({
            "key": k, "ja": m.get("ja"), "ue": m.get("ue"), "scale_m": m.get("scale_m"), "phys": P, "stats": stats,
            "maps": {"basecolor": "basecolor.png", "normal": "normal.png (OpenGL +Y)", "height": "height.png (16bit)",
                     "roughness": "roughness.png", "metallic": "metallic.png", "ao": "ao.png"}},
            ensure_ascii=False, indent=1), encoding="utf-8")
        summary[k] = stats
        rows.append((k, tiles))
        print(k, json.dumps(stats, ensure_ascii=False))
    (cfg["dir"] / "pbr_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(sheet(rows, a.sheet or cfg["dir"] / "pbr_sheet.jpg"))


if __name__ == "__main__":
    main()
