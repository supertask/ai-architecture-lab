"""Comfy Cloud 用のワークフロー / テンプレート引数を作る（生成はしない。送信は Hermes の comfyui MCP で）。

  # 色（ベースカラー）: GPT Image 2.5（OpenAIGPTImageNodeV2、約16〜20クレジット/枚）の API 形式ワークフロー
  uv run -q python scripts/archviz/material/comfy_wf.py gpt-base <materials.json> --out wf.json [--seed 1] [--only k1,k2]
  # 比較用「AIに法線・粗さを直接描かせる」: 先に upload_file した色画像の名前を {key: name} の JSON で渡す
  uv run -q python scripts/archviz/material/comfy_wf.py gpt-aidirect <materials.json> --uploads up.json --out wf.json
  # Qwen-Image 2.1 テンプレート（run_template の引数）。切替ノードの on_false/on_true/switch と未使用側も同じ文で上書き
  uv run -q python scripts/archviz/material/comfy_wf.py qwen --kind t2i|edit --prompt "..." [--image <uploaded>] [--seed 1] --out args.json

送信の手順（Hermes の comfyui MCP）:
  1. estimate_credits で見積もる（指示文のクレジット上限内か）。2枚程度で1回試してから残りを1回で送る。
  2. submit_workflow（無人実行では有料ノードの支払い確認ダイアログが出せず止まることがある。本人の指示文に
     「上限○クレジットで生成可」とあれば confirm: true を付けてよい。購入・トップアップはしない）。
  3. get_output の直後に curl で保存（ダウンロードURLは数分で切れる）→ <dir>/<key>/raw.png（加工しない）。
  4. 保存した画像ごとに生成レシピを残す（目的・入力・モデル。新しいモデルで作り直す用）:
     python -X utf8 scripts/gen_recipe.py write <dir>/<key>/raw.png --args wf.json --node "base <key>" \
         --purpose "<目的。合格条件>" --project P-… [--input <入力画像>]
     （Qwen は --args args.json だけでよい。作り直しは scripts/regen_from_recipe.py）
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import keys_of, load_config  # noqa: E402

SUFFIX = ("Seamless tileable PBR base-color texture, a perfectly flat surface photographed straight-on "
          "(orthographic top view, camera perpendicular to the surface), soft even diffuse lighting with no "
          "directional shadows, no specular hotspots, no vignetting, no perspective, no border, no text, no objects; "
          "the material fills the whole frame edge to edge and the pattern wraps seamlessly on all four edges.")
PROMPT_GUIDE = ("<素材の具体的な見た目を英語で: 材料・粒や繊維の大きさ(mm/cm)・色の名前・仕上げ・本数や間隔を数で>. "
                "The image covers <N> cm x <N> cm.")
AIDIRECT = {
    "normal": "This image is the base color (albedo) texture of a seamless tileable architectural surface material. Generate the matching tangent-space NORMAL MAP for exactly this texture, pixel-aligned with the input, in OpenGL convention (+Y up): flat areas must be pure (128,128,255) lavender blue, raised edges shown with red/green shading. Output only the normal map texture, full frame, seamless, no border, no text, no lighting, no perspective.",
    "roughness": "This image is the base color (albedo) texture of a seamless tileable architectural surface material. Generate the matching grayscale ROUGHNESS MAP for exactly this texture, pixel-aligned with the input: black = glossy/polished, white = fully matte. Output only the grayscale roughness texture, full frame, seamless, no border, no text, no lighting, no perspective.",
}
GPT = {"model": "gpt-image-2.5-flare", "model.size": "1024x1024", "model.custom_width": 1024, "model.custom_height": 1024,
       "model.background": "opaque", "model.quality": "high", "n": 1}
# Qwen-Image 2.1 テンプレートの切替ノード（プロンプト拡張の on/off）と、使われない側のプロンプトノード
QWEN = {"t2i": {"name": "image_qwen_image_2_1_t2i", "switch": "459:474", "unused": "459:471"},
        "edit": {"name": "image_qwen_image_2_1_image_edit", "switch": "459:484", "unused": "459:500"}}


def gpt_node(prompt, seed, title, image_ref=None):
    inp = dict(GPT, prompt=prompt, seed=seed)
    if image_ref:
        inp["model.images.image_1"] = image_ref
    return {"class_type": "OpenAIGPTImageNodeV2", "inputs": inp, "_meta": {"title": title}}


def gpt_base(cfg, seed, only=None, prefix="base"):
    wf, rec, i = {}, {}, 1
    suffix = cfg.get("suffix", SUFFIX)
    for k in keys_of(cfg, only):
        p = cfg["materials"][k]["prompt"].strip() + " " + suffix
        g, s = str(i), str(i + 1)
        i += 2
        wf[g] = gpt_node(p, seed, "%s %s" % (prefix, k))
        wf[s] = {"class_type": "SaveImage", "inputs": {"images": [g, 0], "filename_prefix": "%s_%s" % (prefix, k)},
                 "_meta": {"title": "save " + k}}
        rec[k] = p
    return wf, rec


def gpt_aidirect(cfg, uploads, seed, only=None, prefix="aidirect"):
    wf, i = {}, 1
    for k in keys_of(cfg, only):
        if k not in uploads:
            continue
        li = str(i)
        i += 1
        wf[li] = {"class_type": "LoadImage", "inputs": {"image": uploads[k]}, "_meta": {"title": "base " + k}}
        for m, pr in AIDIRECT.items():
            g, s = str(i), str(i + 1)
            i += 2
            wf[g] = gpt_node(pr, seed, "AI direct %s %s" % (m, k), [li, 0])
            wf[s] = {"class_type": "SaveImage", "inputs": {"images": [g, 0], "filename_prefix": "%s_%s_%s" % (prefix, k, m)},
                     "_meta": {"title": "save %s %s" % (k, m)}}
    return wf


def qwen_args(kind, prompt, image=None, seed=None):
    q = QWEN[kind]
    ov = {q["switch"]: {"switch": False, "on_false": prompt, "on_true": prompt}, q["unused"]: {"prompt": prompt}}
    if seed is not None:
        ov["459:458"] = {"seed": seed}
    if kind == "edit":
        if not image:
            raise SystemExit("--image（upload_file した名前）が要る")
        ov["470"] = {"image": image}
        ov["475"] = {"image": image}
    return {"name": q["name"], "input_overrides": ov, "wait_for_output": True, "client_os": "windows"}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("gpt-base")
    b.add_argument("config")
    b.add_argument("--out", required=True)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--only")
    b.add_argument("--prefix", default="base")
    d = sub.add_parser("gpt-aidirect")
    d.add_argument("config")
    d.add_argument("--uploads", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--seed", type=int, default=1)
    d.add_argument("--only")
    q = sub.add_parser("qwen")
    q.add_argument("--kind", choices=["t2i", "edit"], required=True)
    q.add_argument("--prompt", required=True)
    q.add_argument("--image")
    q.add_argument("--seed", type=int)
    q.add_argument("--out", required=True)
    sub.add_parser("guide")
    a = ap.parse_args()
    if a.cmd == "guide":
        print("prompt:", PROMPT_GUIDE, "\nsuffix:", SUFFIX)
        return
    if a.cmd == "gpt-base":
        cfg = load_config(a.config)
        wf, rec = gpt_base(cfg, a.seed, a.only.split(",") if a.only else None, a.prefix)
        Path(a.out).write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
        Path(a.out).with_name(Path(a.out).stem + "_prompts.json").write_text(
            json.dumps({"prompts": rec, "gpt": GPT, "seed": a.seed}, indent=1, ensure_ascii=False), encoding="utf-8")
        n = len(rec)
    elif a.cmd == "gpt-aidirect":
        cfg = load_config(a.config)
        ups = json.loads(Path(a.uploads).read_text(encoding="utf-8"))
        wf = gpt_aidirect(cfg, ups, a.seed, a.only.split(",") if a.only else None)
        Path(a.out).write_text(json.dumps(wf, indent=1), encoding="utf-8")
        n = sum(1 for v in wf.values() if v["class_type"] == "OpenAIGPTImageNodeV2")
    else:
        Path(a.out).write_text(json.dumps(qwen_args(a.kind, a.prompt, a.image, a.seed), indent=1, ensure_ascii=False), encoding="utf-8")
        n = 1
    print("wrote", a.out, "images:", n, "(GPT Image 2.5 は約16〜20クレジット/枚。送る前に estimate_credits)")


if __name__ == "__main__":
    main()
