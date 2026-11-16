"""AI に渡す「きれいな作業フォルダ」を作る（正解や他の出力が AI から見えないようにするため）。

  python scripts/prepare_run.py A  --out D:/ai-run/A      # 1回目の形式（スクリプトを書かせるだけ。Rhino 接続は不要）
  python scripts/prepare_run.py B  --out D:/ai-run/B
  python scripts/prepare_run.py A --live --out D:/ai-run/liveA   # 2回目の形式（AI が Rhino に部分ごとに送って組む）

できるもの：<out>/inputs/ に入力画像（A は外観だけ、B は外観＋図面）、<out>/prompt.md（パスを <out> に置き換えた指示文）、
空の出力フォルダ。AI にはこのフォルダだけを開かせ、「prompt.md を読んで、その指示どおりに作業してください」とだけ入力する。
このキットのフォルダ（outputs/・scripts/draw_v14.py・outputs/reference_v14.py＝答え）の中で AI を起動しないこと。
標準ライブラリだけで動く（python 3.8 以上）。
"""
import argparse
import re
import shutil
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["A", "B"])
    ap.add_argument("--live", action="store_true", help="2回目（Rhino で部分ごとに組む）の指示文を使う")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if out == KIT or KIT in out.parents:
        raise SystemExit("キットの外に作ってください（中に作ると AI が答えのファイルを見られる）")
    (out / "inputs").mkdir(parents=True, exist_ok=True)
    shutil.copy(KIT / "inputs" / "house_v6C.png", out / "inputs" / "house_v6C.png")
    if a.which == "B":
        shutil.copy(KIT / "inputs" / "drawing_v14.png", out / "inputs" / "drawing_v14.png")
    o = out.as_posix()
    if a.live:
        src = (KIT / "run2_recorded" / "prompts" / ("%s_prompt.md" % a.which)).read_text(encoding="utf-8")
        body = re.sub(r"^<!--.*?-->\s*", "", src, flags=re.S)
        body = body.replace("<REC>/%s_out/" % a.which, o + "/%s_out/" % a.which)
        body = body.replace("<REC>/", o + "/inputs/")
        (out / ("%s_out" % a.which)).mkdir(exist_ok=True)
    else:
        name = "A_image_only_prompt.md" if a.which == "A" else "B_image_plus_drawing_prompt.md"
        src = (KIT / "prompts" / name).read_text(encoding="utf-8")
        body = src[src.index("## Goal"):]
        body = body.split("## 実行時に")[0].rstrip() + "\n"
        body = body.replace("<KIT>", o).replace("<WORKDIR>", o)
        (out / "outputs" / a.which).mkdir(parents=True, exist_ok=True)
    (out / "prompt.md").write_text(body, encoding="utf-8")
    print("作業フォルダ:", o)
    print("AI への入力: 「%s/prompt.md を読んで、その指示どおりに作業してください」" % o)


if __name__ == "__main__":
    main()
