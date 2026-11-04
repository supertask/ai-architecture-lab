# テクスチャの作り方（3種＋木）
共通：ComfyUI（Comfy Cloud）のテンプレート `image_qwen_image_2_1_t2i`（Qwen-Image 2.1）で色画像を1枚作る → `seam.py` で継ぎ目なしに → DeepBump で法線・高さ → `make_pbr.py` で粗さ・AO・金属を計算。

## 打放しコンクリート

- テンプレート：`image_qwen_image_2_1_t2i`　seed：11
- プロンプト（原文）：

```
Orthographic flat texture photo, straight-on, even overcast light, no perspective, no shadows: Japanese architectural exposed fair-faced concrete wall (uchippanashi) in light warm grey. Exactly one formwork panel 900 mm wide x 1800 mm tall fills the image, with crisp thin panel joint lines along the four edges, and six small round form-tie holes (P-cone, 25 mm diameter, recessed, slightly darker grey) in a 2 x 3 grid, 450 mm apart horizontally and 600 mm apart vertically, centred. Smooth surface with very subtle cloudy tonal variation, faint fine air bubbles, a few faint vertical water streaks. No text, no objects.
```

- 後処理：seam → DeepBump → make_pbr（模型には 1.8m 角で貼る）。比較用に色画像を明るさ 0.72・コントラスト 1.25 に調整（compare/make_tex.py）。

## 黒モルタル（金鏝）

- テンプレート：`image_qwen_image_2_1_t2i`　seed：38
- プロンプト（原文）：

```
Orthographic flat texture scan of a real architectural wall surface, straight-on, perfectly even diffuse overcast light, no shadows, no light spots, no vignetting, no stains, no perspective, evenly distributed detail over the whole square for seamless tiling, 1.2 m x 1.2 m area. Black pigmented mortar finished with a steel trowel, near-black graphite colour, burnished cloudy patches and fine trowel strokes, slight sheen variation. Matte. No text, no objects, no frame.
```

- 後処理：seam → DeepBump → make_pbr（粗さ 0.45）。比較用に法線を 75% 平らにして、2.4m 角で貼る（キルト模様を消すため）。

## 版築

- テンプレート：`image_qwen_image_2_1_t2i`　seed：36
- プロンプト（原文）：

```
Orthographic flat texture scan of a real architectural wall surface, straight-on, perfectly even diffuse overcast light, no shadows, no light spots, no vignetting, no stains, no perspective, evenly distributed detail over the whole square for seamless tiling, 1.2 m x 1.2 m area. Rammed earth wall (hanchiku), horizontal compacted layers 50-80 mm thick in natural ochre, brown and sand tones, fine aggregate and small pebbles, subtle layer lines. Matte. No text, no objects, no frame.
```

- 後処理：seam → DeepBump → make_pbr（粗さ 0.9）。比較用に色画像の彩度 0.55・明るさ 0.85、1.5m 角で貼る。

## 木（方立・軒天）

- テンプレート：`image_qwen_image_2_1_t2i`　seed：12
- プロンプト（原文）：

```
Orthographic flat texture photo, straight-on, even light, no perspective: interior wood ceiling of narrow solid wood boards 90 mm wide running vertically, about 13 boards across, light honey-coloured Japanese cypress (hinoki) with fine straight grain and a few small knots, thin dark 3 mm shadow gaps between boards, matte oiled finish. The image covers 1.2 m x 1.2 m. No text, no objects.
```

- 後処理：seam → DeepBump → make_pbr（1.2m 角）。
