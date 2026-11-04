"""素材パイプライン共通: 設定 JSON の読み込みと画像の入出力。

設定 JSON（例 scripts/archviz/material/materials.example.json）:
{
  "dir": "C:/.../<企画>/<版>/materials",         # 素材ごとのフォルダ <dir>/<key>/ を作る
  "suffix": "(省略可) GPT Image に付ける共通文",
  "materials": {
    "<key>": {"ja": "瓦テラゾ", "ue": "Kawara", "scale_m": 0.8, "prompt": "...英文...",
              "phys": {...make_pbr.py の PHYS 説明...}}
  }
}
フォルダ内のファイル名（固定）:
  raw.png               … 画像AIの出力（加工しない）
  basecolor_src.png     … 継ぎ目を直した色（seam.py fix）
  normal_deepbump.png / height_deepbump.png … DeepBump（deepbump.py）
  basecolor.png normal.png(OpenGL) height.png(16bit) roughness.png metallic.png ao.png material.json … make_pbr.py
  ai/normal.png ai/roughness.png … 比較用の「AIに直接描かせた」マップ（任意、加工しない）
"""
import json
from pathlib import Path

# numpy / Pillow は画像を扱う関数の中で読む（comfy_wf.py・deepbump.py は numpy 無しで動かすため）


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg["dir"] = Path(cfg["dir"])
    return cfg


def mat_dir(cfg, key):
    d = cfg["dir"] / key
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_rgb(p, size=None):
    import numpy as np
    from PIL import Image
    im = Image.open(p).convert("RGB")
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im).astype(np.float64) / 255.0


def load_gray(p, size=None):
    import numpy as np
    from PIL import Image
    im = Image.open(p)
    if im.mode in ("I;16", "I;16B", "I"):
        a = np.asarray(im).astype(np.float64) / 65535.0
        if size:
            a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)) / 255.0
        return a
    im = im.convert("L")
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im).astype(np.float64) / 255.0


def save8(a, p):
    import numpy as np
    from PIL import Image
    a = np.clip(a, 0, 1)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8), "L" if a.ndim == 2 else "RGB").save(p)


def save16(a, p):
    import numpy as np
    from PIL import Image
    Image.fromarray((np.clip(a, 0, 1) * 65535 + 0.5).astype(np.uint16)).save(p)


def keys_of(cfg, only=None):
    ks = list(cfg["materials"].keys())
    return [k for k in ks if not only or k in only]
