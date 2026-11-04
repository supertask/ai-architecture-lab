"""DeepBump で色画像から法線（OpenGL）と高さを作る。1枚 1024px で約10秒（CPU, onnxruntime）。

  uv run -q python scripts/archviz/material/deepbump.py <basecolor.png> <out_dir>
  uv run -q python scripts/archviz/material/deepbump.py --config <materials.json> [--only k1,k2]
出力: <out_dir>/normal_deepbump.png, height_deepbump.png（normals_to_height seamless=TRUE）
DeepBump 本体の場所: --deepbump か 環境変数 DEEPBUMP_DIR（既定 work/app-sandbox/tools/DeepBump, GPL-3.0, commit fad19ba）。
実行は uv で Python 3.12 + onnxruntime + imageio + numpy を一時環境に入れる（3.14 では onnxruntime が無い）。
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import keys_of, load_config, mat_dir  # noqa: E402

DEFAULT_DB = Path(__file__).resolve().parents[3] / "work" / "app-sandbox" / "tools" / "DeepBump"
UV = ["uv", "run", "-q", "--no-project", "--python", "3.12", "--with", "onnxruntime", "--with", "imageio", "--with", "numpy", "python"]


def run(src, out_dir, db_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cli = str(Path(db_dir) / "cli.py")
    n = out_dir / "normal_deepbump.png"
    h = out_dir / "height_deepbump.png"
    t0 = time.time()
    # DeepBump は RGB 3ch 前提。PNG にアルファがあると落ちるので一旦 RGB に揃える
    from PIL import Image
    tmp = out_dir / "_db_in.png"
    Image.open(src).convert("RGB").save(tmp)
    subprocess.run(UV + [cli, str(tmp), str(n), "color_to_normals", "--color_to_normals-overlap", "LARGE"], check=True, cwd=db_dir)
    subprocess.run(UV + [cli, str(n), str(h), "normals_to_height", "--normals_to_height-seamless", "TRUE"], check=True, cwd=db_dir)
    tmp.unlink(missing_ok=True)
    return {"normal": str(n), "height": str(h), "sec": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("out_dir", nargs="?")
    ap.add_argument("--config")
    ap.add_argument("--only")
    ap.add_argument("--deepbump", default=os.environ.get("DEEPBUMP_DIR", str(DEFAULT_DB)))
    a = ap.parse_args()
    if a.config:
        cfg = load_config(a.config)
        for k in keys_of(cfg, a.only.split(",") if a.only else None):
            d = mat_dir(cfg, k)
            print(k, run(d / "basecolor_src.png", d, a.deepbump))
    else:
        print(run(a.src, a.out_dir, a.deepbump))


if __name__ == "__main__":
    main()
