# 技術メモ：外観だけ vs 外観＋図面（詳しい人向け）

建築家向けの説明は [README.md](README.md)、AI が従う手順は [AI_GUIDE.md](AI_GUIDE.md) にあります。
ここには、ファイルの一覧・手順の細部・撮影と採点・テクスチャ・パスの扱いをまとめています。

## AI と Rhino の接続

- セットアップの手順書：https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T
- ワークショップのスライド：https://docs.google.com/presentation/d/11fd7nvZPuE5BPmIBTQYlUanp_OZPNibPhbAnpD_UStg/edit?usp=sharing
  - ChatGPT のデスクトップアプリで Codex を開く（実行権限は「フルアクセス」）→ 配布ページのプロンプトを貼る → AI の案内どおりに Rhino／Grasshopper（または Archicad）との接続をインストール・設定 → 接続テストとして「バルセロナ・パビリオン」を作らせる。
- この実験で使った接続は、Rhino 用の MCP サーバー（[supertask/rhino-mcp](https://github.com/supertask/rhino-mcp)。AI から Rhino 内で Python を実行できる）。同じ働きのものなら何でもよい。
- **1回目の形式（AI はスクリプトを書くだけ）なら、AI と Rhino の接続は不要。** Rhino で `scripts/run_all_in_rhino.py` を自分で実行すれば、撮影・採点まで進める。

## 手順（コマンド）

### 1. 自分のエージェントに指示を渡す

Claude Code・Codex・Hermes Agent のどれでも同じ。

1. AI が答えを見られないよう、入力だけを入れた別フォルダを作る（キットのフォルダの中で、模型を作らせる AI を起動しない。`outputs/reference_v14.py` と `scripts/draw_v14.py` が答えそのもの）：
   ```
   python scripts/prepare_run.py A --out D:/ai-run/A          # 絵だけ
   python scripts/prepare_run.py B --out D:/ai-run/B          # 絵＋図面
   # Rhino に部分ごとに送って組ませる（2回目・録画回の形式）なら --live を付ける
   ```
2. そのフォルダで**新しい会話**を始め（過去の会話・メモリ・スキルなし）、次の1文だけを入力する：
   「`D:/ai-run/A/prompt.md` を読んで、その指示どおりに作業してください」
   - Claude Code：フォルダで `claude` を起動して入力。Codex：デスクトップアプリでフォルダを追加して入力。Hermes Agent：ターミナルで起動して入力。
   - 指示文にある `vision_analyze`（画像を見る）・`execute_rhino_code`（Rhino で Python を実行）は Hermes でのツール名。他のエージェントでは、同じ働きのツール（画像の読み込み、Rhino 接続の実行ツール）が使われる。
3. A と B は別の会話で、同じ AI モデルで行う。できた `model.py` を `outputs/A/`・`outputs/B/` に置き換える（元の出力と比べたいなら別名で置き、`scripts/run_all_in_rhino.py` に行を足す）。
   - 出力の場所：1回目の形式は `<out>/outputs/A/`、`--live` は `<out>/A_out/`（どちらも `model.py`・`params.json`・`notes.md`）。

### 2. 撮影と採点

1. `scripts/run_compare.py` と `scripts/run_all_in_rhino.py` の先頭の `KIT = 'C:/path/to/kit/'` を、このフォルダの絶対パスに書き換える。
2. Rhino で `scripts/run_all_in_rhino.py` を実行（ScriptEditor で開いて実行、または AI に「このファイルを Rhino で実行して」）→ `work/compare/<名前>/` に影絵と比較画像。**途中で Rhino の窓の大きさを変えない**（縮尺が変わる）。
3. 採点：`uv run -q --with pillow --with numpy python scripts/metrics.py`（1回目）／`scripts/metrics_live.py`（2回目）→ `results/`・`run2_recorded/results/`。
4. 比較シート：`uv run -q --with pillow python scripts/sheets.py`。

**Rhino なしで採点だけ確かめる**：検証時の影絵を `results/silhouettes/` に入れてある。
`uv run -q --with pillow --with numpy python scripts/metrics_live.py results/silhouettes` で、公開した2回目の数値（`run2_recorded/results/metrics_live.json`）と同じ値が出る（確認済み。1回目は下の「再現できないもの」を参照）。

### 手順（中身）

1. AI に `prompts/A_…md` の指示と外観画像だけを渡し、`model.py` を書かせる（Rhino は実行させない）。
2. 別の会話で、`prompts/B_…md` の指示と外観画像＋図面を渡し、同じように書かせる。
3. Rhino で `scripts/run_all_in_rhino.py` を実行（中で `run(model.py のパス, 名前, ALIGN, ('concrete','black_mortar','rammed_earth'))` を呼ぶ）。
   - 模型を作る → 地面と道路を共通のものに差し替え → 素材を共通で付ける → 同じカメラで撮る（外観と同じ角度・裏の左右・右前・斜め上、形の比較用に真上・正面・右側面・裏の平行投影）。
   - A は原点を「建物の左端・一番前」に合わせる（ALIGN=True。画像だけでは原点が決まらないため）。正解と B は ALIGN=False。
4. `scripts/metrics.py`：平行投影の影絵を重ね、±3m の範囲で一番重なる位置に平行移動してから、重なり率（IoU）・足りない割合・余分な割合を出す。
5. `scripts/sheets.py`：比較画像を作る。

## 再現できないもの（詳しく）

- **AI の答えは毎回変わる**。同じ指示・同じモデルでも寸法の仮定（目の高さなど）が変わり、A の重なり率は回ごとに数ポイント動く。傾向（A は 70〜80% 前後、B は 90% 台）を見る。
- **AI モデルは更新される**。2026年11月4〜5日の Claude Opus 5.5 での結果。
- **図面づくりの往復は、人の判断そのもの**。描き込みの過程は Figma ボードで見られるが、自分で往復すれば違う図面になる。B を同じ条件で試すなら `inputs/drawing_v14.png` をそのまま使う。
- **画像生成は同じ画素にならない**。外観の絵（`inputs/house_v6C.png`）は生成済みの画像を同梱（絵を生成し直す手順は入れていない）。テクスチャもプロンプトと seed は同じでも、クラウド側のモデル更新で絵は変わる。比較に使ったテクスチャ（`tex/`）は同梱。
- **1回目の数値は、同梱の影絵で再計算すると最大 0.5 ポイントずれる**。1回目の採点のあとで正解の影絵を撮り直したため（2回目は完全に一致）。
- 録画（画面の動画）は X に載せたものだけで、録画・編集の手順は入れていない。

## 入っているもの

- `README.md`（建築家向け）・`AI_GUIDE.md`（AI 向けの手順）・`TECHNICAL.md`（このファイル）
- `inputs/house_v6C.png`：外観（AI 画像、架空の家）
- `inputs/drawing_v14.png`：Figma で人と往復して整えた図面（1階平面・正面・左側面・2階平面、1マス＝1m）（公開版は図の題名から人名だけ外している。図の中身は B に渡したものと同じ）
  - 往復の過程（人の描き込み r1〜r9 と AI の書き出し v7〜v14）は Figma ボードで見られる（閲覧のみ）：https://www.figma.com/board/Fajd8nO7JFtNX5Ty2JOus4
- `prompts/A_image_only_prompt.md`・`prompts/B_image_plus_drawing_prompt.md`：AI に渡した指示（原文そのまま）
- `prompts/textures.md`：テクスチャのプロンプトと後処理
- `outputs/A/`・`outputs/B/`：AI が書いた模型スクリプト `model.py`、仮定した寸法 `params.json`、メモ `notes.md`
- `outputs/reference_v14.py`：正解の模型（図面どおり）
- `run2_recorded/`：2回目（Rhino に部分ごとに送って組んだ録画回）の指示・出力・結果
- `scripts/`
  - `prepare_run.py`：AI に渡すきれいな作業フォルダを作る
  - `run_compare.py`・`run_all_in_rhino.py`：Rhino で模型を実行して同じ条件で撮る
  - `metrics.py`・`metrics_live.py`：重なり率（IoU）を出す。`sheets.py`：比較シート
  - `draw_v14.py`：図面 `inputs/drawing_v14.png` を描いたスクリプト（実行すると題名の行以外は同じ画像になる。確認済み）
  - `comfy_wf.py`・`seam.py`・`deepbump.py`・`make_pbr.py`・`common.py`：テクスチャの生成と PBR 化。`make_tex.py`：比較用の見せ方の調整
  - `fontutil.py`：日本語フォントを OS ごとに探す
- `tex/`：比較に使ったテクスチャ（打放し・黒モルタル・版築・木。色・法線・粗さ・AO）、設定 `materials.json`、外観に寄せた打放しの作り方 `concrete_v6_src/`
- `results/`：比較画像、`metrics.json`、検証時の影絵 `silhouettes/`
- `skills/`：この実験の作業手順を、どのエージェントにも渡せる形にまとめたもの（[skills/README.md](skills/README.md)）

## 使ったもの

- AI：Claude Opus 5.5（Hermes Agent 経由。1回目はサブエージェント、2回目は新しい会話。どちらもこれまでの会話は渡していない）
- Rhino ＋ RhinoCommon（Python スクリプトとして実行）。2回目の AI からの操作は Rhino 用 MCP サーバー
- 図面：Figma（FigJam）＋ iPad
- テクスチャ：ComfyUI（Comfy Cloud）Qwen-Image 2.1 t2i → seam → DeepBump → make_pbr
- 画像処理：Python 3 ＋ Pillow ＋ NumPy（`uv run --with …` で一時環境に入れる）

## 結果の細部

### 1回目（スクリプトを書かせた回、2026-11-04、1回ずつ）

結果の表は [README.md](README.md)。数値は `results/metrics.json`。

正直に書いておくこと：A の `model.py` は、そのままだと壁が消えた（面の向きが内向き）。向きを直す 3 行だけ足して実行した（寸法は変えていない）。正解も図面どおりの模型なので、図面を渡した B に有利な比べ方。1 回ずつの試行。家は架空（AI 画像から作った）。

### 2回目（録画した回、2026-11-04）

同じ比較を、AI が Rhino に部分ごとに送って組み上げる形でもう一度やり、画面を録画した。note の見出しの数値（絵だけ 68〜80%、図面あり 96〜100%）はこの回のもの。

- 指示：`run2_recorded/prompts/A_prompt.md`・`B_prompt.md`（1回目と同じ文面に「Rhino で部分ごとに組む」を足しただけ。入力・出力のフォルダは公開用に `<REC>/` と書き換えた）
- AI：Hermes Agent（Claude Opus 5.5）をターミナルで起動し、新しい会話で「（作業フォルダ）/A_prompt.md を読んで、その指示どおりに作業してください」とだけ入力。同じ準備は `python scripts/prepare_run.py A --live --out <フォルダ>` でできる
- 出力：`run2_recorded/outputs/A`・`B`、結果：`run2_recorded/results/`（`metrics_live.json`、`overlap_sheet_live.png`、`cmp_live.jpg`）
- A は大きさの仮定（絵を撮ったカメラの高さ）が1回目 2.1m・2回目 1.62m と変わり、形も毎回変わった。
- B は2回とも図面に書いてある所は正確。ずれたのは図面に無い所（右端の平屋のまわり、凹みの天井の素材）。

## 外壁のテクスチャ

- 比較に使った3種＋木：`tex/materials.json`（プロンプト・seed・物性値）を使い、ComfyUI で色を生成 → `seam.py config` → `deepbump.py --config` → `make_pbr.py`（出力は `work/materials/`）→ `make_tex.py` で比較用に調整して `tex/` へ。詳しくは [skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md)。
- 外観に寄せたグレーの打放し `tex/concrete_v6_src/`：ComfyUI の Qwen-Image 2.1（画像編集、入力＝外観画像）で作った素地 6 枚、プロンプト原文（`PROMPTS.md`）、組み立てスクリプト `make_concrete_v6.py`
  - `uv run --with pillow --with numpy python tex/concrete_v6_src/make_concrete_v6.py` で 14.4m 角・4096px のシームレスなテクスチャ（basecolor / normal / roughness / AO / height）を `tex/concrete_v6/` に作る。サイズが大きいので生成物はリポジトリに入れていない。

## パスについて

- スクリプト内の `C:/path/to/kit/` は、このフォルダを置いた場所に読み替える（`run_compare.py`・`run_all_in_rhino.py`・`outputs/reference_v14.py` の先頭）。
- 指示文の `<KIT>`・`<REC>` は、`scripts/prepare_run.py` が作業フォルダのパスに置き換える。
- 撮影は Rhino の Rendered 表示を `ViewCapture` で保存している。Rhino の窓の大きさを変えると平行投影の縮尺が変わるので、全模型を同じ窓の状態で撮る。
- 生成物（`work/`）と DeepBump 本体（`tools/`）は `.gitignore` でリポジトリから外している。
