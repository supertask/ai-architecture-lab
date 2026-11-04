# concrete_v6（外観 v6 に寄せたグレーの打放し）の作り方

1. ComfyUI（Comfy Cloud）テンプレート `image_qwen_image_2_1_image_edit`（Qwen-Image 2.1 画像編集）。入力画像は外観 v6C（1678×937）。
2. 素地（Pコン・目地なし）を 6 枚：
   - seed 71, 72, 73（プロンプト A）
   - seed 81, 82, 83（プロンプト B）
3. `uv run --with pillow --with numpy python make_concrete_v6.py` → `../tex/concrete_v6/`（basecolor / height / normal / roughness / ao / metallic、4096px = 14.4m 角）
4. Rhino では箱マッピング 14400mm で貼る（`run_compare.py` の TEX['concrete_v6']）。

## プロンプト A（seed 71〜73）
Create a flat orthographic close-up texture of the bare concrete surface of the house walls in image 1: same light neutral grey colour and same soft cloudy tonal variation, fine pinholes and very subtle vertical flow marks. Show ONLY plain concrete between the form-tie holes: NO form-tie holes, NO panel joints, NO lines, no stains, no dark spots. Straight-on, perfectly even diffuse light, no shadows, no light patterns, no building, no sky. About 1.8 m x 1.8 m of wall filling the frame, evenly detailed for seamless tiling. Photoreal, no text.

## プロンプト B（seed 81〜83）
Create a flat orthographic close-up texture of the bare concrete surface of the house walls in image 1: same warm light grey colour, large soft cloudy blotches of slightly lighter and darker grey, fine scattered pinholes. Show ONLY plain concrete: NO form-tie holes, NO panel joints, NO lines, NO vertical streaks, no stains, no dark spots. Straight-on, perfectly even diffuse light, no shadows, no light patterns, no building, no sky. About 1.8 m x 1.8 m of wall filling the frame. Photoreal, no text.

## リピート感を消す要点（失敗から）
- AI にPコン付きのテクスチャを描かせると、間隔がばらつき、継ぎ目で目立つ → Pコン・目地はプログラムで描く。
- パネルごとに別の AI 画像を貼ると、染みが縁で切れて継ぎはぎ（市松）に見える → AI 画像からは細かい質感だけ（ぼかし成分を引く）使い、大きなむらは FFT の低域ノイズでパネルをまたいで付ける。
- sin 波で大きなむらを作ると斜めの帯になる → FFT ノイズにする。
- 7.2m 角だと家の正面で 2 回以上繰り返して見える → 14.4m 角。
- 色は目で合わせず、元画像と模型の撮影結果の「無彩色画素の中央値」を測って合わせる（v6: 163,161,161 → 模型 163,163,165）。
