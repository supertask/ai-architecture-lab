---
name: pbr-texture-pipeline
description: 画像生成 AI（ComfyUI の Qwen-Image 2.1）で素材の色を作り、継ぎ目修正 → DeepBump → 計算で PBR 一式を作る。リピート感の消し方込み。
---

# 素材（PBR）づくり：色は画像生成 AI、凹凸は DeepBump、粗さ・AO は計算

## 流れ（1素材 約20秒＋生成時間）
1. **設定を書く**：`tex/materials.json` を写し、素材ごとに `prompt`（英語、寸法と数で具体的に）・`scale_m`（1枚の実寸）・`seed`・`phys`（物性値。意味は `scripts/make_pbr.py` の先頭）。
2. **色を生成**：ComfyUI のテンプレート `image_qwen_image_2_1_t2i`（Qwen-Image 2.1）にプロンプトと seed を入れて実行 → `work/materials/<key>/raw.png`（加工しない）。
   - AI から ComfyUI を操作できる場合は `scripts/comfy_wf.py qwen --kind t2i --prompt "…" --seed N --out args.json` で引数を作って送る。
3. **継ぎ目**：`uv run -q --with numpy --with pillow python scripts/seam.py config tex/materials.json` → `basecolor_src.png`。
4. **法線・高さ**：DeepBump（https://github.com/HugoTini/DeepBump 、GPL-3.0）を `tools/DeepBump` に置き、`uv run -q --with pillow python scripts/deepbump.py --config tex/materials.json`。
5. **粗さ・金属・AO**：`uv run -q --with numpy --with pillow --with scipy python scripts/make_pbr.py tex/materials.json` → `basecolor / normal(OpenGL) / height(16bit) / roughness / metallic / ao` と確認用シート。

## プロンプトの型
- 共通の頭：「Orthographic flat texture scan of a real architectural wall surface, straight-on, perfectly even diffuse overcast light, no shadows, no light spots, no vignetting, no stains, no perspective, evenly distributed detail over the whole square for seamless tiling, 1.2 m x 1.2 m area.」＋素材の1〜2文＋「Matte. No text, no objects, no frame.」
- 位置で偏る特徴（汚れ・下の方の湿り）を書かない。下端に黒い帯が描かれ、貼ると等間隔に繰り返す。
- 影を焼き込む「raking light」は書かない。

## AI に法線・粗さを直接描かせない理由
- 画像 AI に法線を描かせると、平らな所が (128,128,255) にならず面全体が 6〜14° 傾く。
- 粗さは色の明るさをなぞる（相関 0.8 超）。凹凸は DeepBump、粗さ・金属度は物性値から計算する方が素直。

## 打放しコンクリートで「リピート感」を消す（`tex/concrete_v6_src/`）
- 「seamless」と頼んでも継ぎ目は残る（継ぎ目比 3〜12）。継ぎ目を直しても、同じ染みが等間隔に並べばリピートは見える。
- Pコン・目地は AI に描かせない（間隔がばらつき、継ぎ目で目立つ）。**プログラムで正確に描く**。
- AI の素地からは細かい質感（気泡・砂目）だけを使い、大きなむらは FFT の低域ノイズでパネルをまたいで付ける（sin 波だと斜めの帯になる）。
- タイルは主な立面より大きく（家の幅 17m なら 14.4m 角）。
- 色は目で合わせず、元画像と模型の撮影結果の「無彩色画素の中央値」を測って合わせる。
- 2×2 に並べた確認画像と、模型に貼った撮影の両方で、繰り返し・市松・横帯を見てから使う。

## Rhino に貼るとき
- 素材をレイヤーに付け、各物体に箱マッピング（`TextureMapping.CreateBoxMapping`、一辺 = scale_m × 1000 mm）。
- 同じ文書でスクリプトを2回目以降に流すときは、レイヤーを `FindByFullPath` で探して再利用する（同名で `Layers.Add` すると -1 が返り、素材が全部外れる）。
- Rhino の Rendered 表示では、粗さ・AO・高さの差はほぼ見えない。質感を評価するならレンダラー（Unreal など）で。

## 画像編集（Qwen-Image 2.1 edit）を使うときの注意
- 編集のたびに画像が劣化する（ざらつき・汚れが増える）。毎回**元の画像から1回で**編集し、編集結果に重ねて編集しない。
- 場所ごとに違う形の編集（「この角だけ丸く」）は文章では効きにくい。形は 3D で決め、AI は質感だけに使う。
