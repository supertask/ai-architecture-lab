🇯🇵 日本語 | [🇺🇸 English](AI_GUIDE.en.md)

# AI_GUIDE：この実験を再現する AI エージェントへの手引き

あなた（AI エージェント）は、このフォルダ（以下 **キット**）を使って、建築家のユーザーと一緒に
「外観の絵1枚だけ（A）／絵＋図面（B）で AI に Rhino 模型を作らせ、正解の模型との重なり率で比べる」を再現します。
人向けの説明は [README.md](README.md) です。AI が知っておくこと（ファイル、コマンド、実験で実際にやったこと、困った時の対処）は、このファイルにまとめてあります。

## 1. 基本の動き方

**手順の本体は `prompts/` の指示ファイルです。** ユーザーは各段で、次の形の1行を貼ります。
「`<指示ファイル>` を読んで、指示どおりに作業してください」
指示ファイルの名前が無いまま頼まれた時は、下の表で今どの段かを判断し（`work/progress.md` があれば読む）、その段の指示ファイルを読んで進めてください。

## 2. いちばん大事な決まり：キットを開いているあなたは模型を作らない

キットには正解が入っています（`outputs/reference_v14.py`、`scripts/draw_v14.py`、`outputs/`、`run2_recorded/outputs/`、`results/`）。
A・B の模型は、入力だけを入れた別のフォルダ（`ai-run-A`・`ai-run-B`）で、**新しい会話の AI** が作ります。あなたの役目は、準備・撮影・採点・説明です。正解の中身（寸法など）を、ユーザーや模型を作る AI に伝えないでください。

## 3. 段と指示ファイル

| 段 | 作業フォルダ | ユーザーが貼る1行の中のファイル | 中身 |
| --- | --- | --- | --- |
| 0 | キット | `prompts/00_prepare_A.md` | 形式（Rhino で組む／スクリプトだけ）を決め、`prepare_run.py A` で `../ai-run-A` を作る |
| 1 | ai-run-A（新しい会話） | `prompt.md` | 模型を作る（実験の指示の原文。キットの AI は関わらない） |
| 2 | キット | `prompts/00_prepare_B.md` | `../ai-run-B` を作る |
| 3 | ai-run-B（新しい会話） | `prompt.md` | 模型を作る |
| 4 | キット | `prompts/10_shoot_and_score.md` | 模型を `work/mine/` に集め、`make_rhino_runner.py` → Rhino で撮影 → `metrics.py --out work/results_mine` |
| — | キット | `prompts/11_check_scoring.md` | Rhino 無しで、同梱の影絵から録画回の数値を再計算（`metrics_live.py --out work/results_check`） |

- 段 1・3 の会話には、キットの話やほかの資料を渡さない（条件が変わるため）。A と B は別々の会話で、同じ AI モデルで行う。

## 4. どの段でも守る決まり

1. **ユーザーは建築家で、プログラマーではない。** 返事はユーザーと同じ言語で、建築の言葉で短く。コマンド、パス、プログラム用語（JSON、IoU、Python、MCP など）を見せない（IoU →「重なり率」）。
2. **コマンドは全部あなたが実行する。** Python や画像処理の道具を入れる時は、先に許可を取る。
3. **人に頼むのは、新しい会話を始めることと、Rhino の画面に関わる操作だけ。** 何をどこに貼るかまで具体的に書く。
4. **Rhino に命令を送るのは、いつも1つの AI だけ。** 模型を作る会話が Rhino を使っている間は、あなたは Rhino に何も送らない。
5. **公開済みの結果（`results/`・`run2_recorded/results/`・`outputs/`）を上書きしない。** あなたの結果は `work/` に。
6. **結果を作らない。** 失敗したら平易に伝え、次の手を提案する。
7. つながらない時は、セットアップ資料（日本語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja ／英語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en）を案内する。
8. 指示文にある `vision_analyze`（画像を見る）・`execute_rhino_code`（Rhino で Python を実行）は、実験で使ったエージェント（Hermes Agent）のツール名。ほかのエージェントでは、同じ働きのツール（画像の読み込み、Rhino 接続の実行ツール）に読み替える。

## 5. ファイルとスクリプト

- `README.md`・`README.en.md`：人（建築家）向け。`AI_GUIDE.md`・`AI_GUIDE.en.md`：このファイル
- `inputs/house_v6C.png`：外観（AI 画像、架空の家）
- `inputs/drawing_v14.png`：Figma で人と往復して整えた図面（1階平面・正面・左側面・2階平面、1マス＝1m）。公開版は図の題名から人名だけ外している（図の中身は B に渡したものと同じ）
- `prompts/A_image_only_prompt.md`・`prompts/B_image_plus_drawing_prompt.md`：1回目に模型を作る AI に渡した指示の原文（下の「9」）
- `prompts/00_prepare_A.md`・`00_prepare_B.md`・`10_shoot_and_score.md`・`11_check_scoring.md`：README の各段で AI が読む指示（公開用に書いた）
- `prompts/textures.md`：テクスチャのプロンプトと後処理
- `outputs/A/`・`outputs/B/`：1回目に AI が書いた模型 `model.py`、仮定した寸法 `params.json`、メモ `notes.md`。**正解ではないが、公開済みの結果なので上書きしない**
- `outputs/reference_v14.py`：正解の模型（図面どおり）。**模型を作る AI に見せない**
- `run2_recorded/`：2回目（Rhino に部分ごとに送って組んだ録画回）の指示（`prompts/A_prompt.md`・`B_prompt.md`）・出力・結果
- `results/`：比較画像、`metrics.json`、検証時の影絵 `silhouettes/`
- `tex/`：比較に使ったテクスチャ（打放し・黒モルタル・版築・木。色・法線・粗さ・AO）、設定 `materials.json`、外観に寄せた打放しの作り方 `concrete_v6_src/`
- `skills/`：作業手順（[skills/README.md](skills/README.md)）
- `images/`：README の画像
- `scripts/`：

| スクリプト | 役目 |
| --- | --- |
| `prepare_run.py A` / `B` `--out <フォルダ> [--live]` | 入力だけのきれいな作業フォルダを作り、`prompt.md` を置く。`--live` は2回目（Rhino で部分ごとに組む）の指示を使う |
| `make_rhino_runner.py [--only A]` | `work/mine/A/`・`B/` の模型を正解と同じ条件で撮る Rhino 用ファイル `work/run_mine_here.py` を作る（キットの場所を書き込み済み） |
| `run_compare.py`・`run_all_in_rhino.py` | Rhino で模型を実行し、同じ条件で撮る（公開した模型を撮り直す時。先頭の `KIT` を書き換える） |
| `metrics.py`・`metrics_live.py` | 影絵から重なり率（IoU）を出す（1回目用・2回目用）。引数 `[影絵のフォルダ] [--out 書き出し先] [--tags …]` |
| `sheets.py` | 比較シートを作る |
| `draw_v14.py` | 図面 `inputs/drawing_v14.png` を描いたスクリプト（実行すると題名の行以外は同じ画像。確認済み）。**正解の一部なので模型を作る AI に見せない** |
| `comfy_wf.py`・`seam.py`・`deepbump.py`・`make_pbr.py`・`common.py` | テクスチャの生成と PBR 化 |
| `make_tex.py` | テクスチャの比較用の見せ方を調整 |
| `fontutil.py` | 日本語フォントを OS ごとに探す |

必要な物：Rhino（撮影。RhinoCommon の Python スクリプトとして実行）、Python 3 ＋ Pillow ＋ NumPy（`uv run --with …` で一時環境に入れる）。

## 6. AI と Rhino の接続

- 実験で使った接続は、Rhino 用の MCP サーバー（[supertask/rhino-mcp](https://github.com/supertask/rhino-mcp)。AI から Rhino 内で Python を実行できる）。同じ働きのものなら何でもよい。
- **スクリプトだけの形式（1回目の形式）なら、AI と Rhino の接続は不要。** 撮影の時だけ、`work/run_mine_here.py` をユーザーに Rhino の ScriptEditor で開いて実行してもらう。
- 段 0・2 の指示は、Rhino を AI から動かせるかを確かめ、動かせれば「Rhino で部分ごとに組む」形式（`--live`）、無ければスクリプト形式でフォルダを作る。

## 7. コマンドの細部

### 模型を作るフォルダの準備（段 0・2）

キットのフォルダの中で、模型を作る AI を起動しない（`outputs/reference_v14.py` と `scripts/draw_v14.py` が答えそのもの）。段 0・2 の指示は、次をキットの隣（`../ai-run-A`・`../ai-run-B`）に対して行う。

```
python scripts/prepare_run.py A --out ../ai-run-A          # 絵だけ
python scripts/prepare_run.py B --out ../ai-run-B          # 絵＋図面
# Rhino に部分ごとに送って組ませる（2回目・録画回の形式）なら --live を付ける
```

- 段 1・3：そのフォルダで**新しい会話**（過去の会話・メモリ・スキルなし）を始め、「`prompt.md` を読んで、指示どおりに作業してください」の1行だけ。Claude Code ならフォルダで `claude` を起動して入力、Codex ならデスクトップアプリでフォルダを追加して入力。
- 出力の場所：スクリプト形式は `<out>/outputs/A/`、`--live` は `<out>/A_out/`（どちらも `model.py`・`params.json`・`notes.md`。B も同様）。

### 撮影と採点（段 4）

`prompts/10_shoot_and_score.md` の流れ：
1. 模型を `work/mine/A/`・`work/mine/B/` に集める（`params.json`・`notes.md` も）。公開の `outputs/` は上書きしない。
2. `python scripts/make_rhino_runner.py` → `work/run_mine_here.py`
3. Rhino で `work/run_mine_here.py` を実行（接続があればあなたが、無ければユーザーが ScriptEditor で）→ `work/compare/<名前>/` に影絵と比較画像。**途中で Rhino の窓の大きさを変えない**（縮尺が変わる）。
4. `uv run -q --with pillow --with numpy python scripts/metrics.py work/compare --out work/results_mine`

### Rhino なしで採点だけ確かめる

```
uv run -q --with pillow --with numpy python scripts/metrics_live.py results/silhouettes --out work/results_check
```

公開した2回目の数値（`run2_recorded/results/metrics_live.json`）と同じ値が出る（確認済み。数分かかる）。`prompts/11_check_scoring.md` と同じこと。1回目の数値は、同梱の影絵で再計算すると最大 0.5 ポイントずれる（1回目の採点のあとで正解の影絵を撮り直したため。2回目は完全に一致）。

### 公開した模型を撮り直す（手で）

1. `scripts/run_compare.py` と `scripts/run_all_in_rhino.py` の先頭の `KIT = 'C:/path/to/kit/'` を、キットの絶対パスに書き換える。
2. Rhino で `scripts/run_all_in_rhino.py` を実行 → `work/compare/<名前>/`。
3. 採点：`uv run -q --with pillow --with numpy python scripts/metrics.py`（1回目）／`scripts/metrics_live.py`（2回目）。**`--out <フォルダ>` を付けないと公開済みの `results/`・`run2_recorded/results/` を上書きする**ので、必ず `--out work/…` を付ける。`--tags A_image_only,B_image_plus_drawing` で採点する模型を絞れる。
4. 比較シート：`uv run -q --with pillow python scripts/sheets.py`。

## 8. 撮影と採点の中身

- `run_all_in_rhino.py` は、模型ごとに `run(model.py のパス, 名前, ALIGN, ('concrete','black_mortar','rammed_earth'))` を呼ぶ。
- 模型を作る → 地面と道路を共通のものに差し替え → 素材を共通で付ける → 同じカメラで撮る（外観と同じ角度・裏の左右・右前・斜め上、形の比較用に真上・正面・右側面・裏の平行投影）。
- A は原点を「建物の左端・一番前」に合わせる（ALIGN=True。画像だけでは原点が決まらないため）。正解と B は ALIGN=False。
- 撮影は Rhino の Rendered 表示を `ViewCapture` で保存する。Rhino の窓の大きさを変えると平行投影の縮尺が変わるので、全模型を同じ窓の状態で撮る。
- `metrics.py`：平行投影の影絵を重ね、±3m の範囲で一番重なる位置に平行移動してから、重なり率（IoU）・足りない割合・余分な割合を出す。

## 9. 実験で実際にやったこと

AI は Claude Opus 5.5（Hermes Agent 経由）。図面は Figma（FigJam）＋ iPad。2026年11月4〜5日。

### 1回目（スクリプトを書かせた回、2026-11-04）

- 模型を作る AI は Hermes Agent のサブエージェント（これまでの会話は渡していない）。Rhino は実行させず、`model.py` を書かせた。A は絵だけ、B は絵＋図面。1回ずつ。
- A の `model.py` は、そのままだと壁が消えた（面の向きが内向き）。向きを直す3行だけ足して実行した（寸法は変えていない）。
- 数値：`results/metrics.json`。

### 2回目（録画した回、2026-11-04）

- 同じ比較を、AI が Rhino に部分ごとに送って組み上げる形でもう一度やり、画面を録画した。note 記事の見出しの数値（絵だけ 68〜80%、図面あり 96〜100%）はこの回のもの。
- Hermes Agent をターミナルで起動し、新しい会話で「（作業フォルダ）/A_prompt.md を読んで、その指示どおりに作業してください」とだけ入力。同じ準備は `python scripts/prepare_run.py A --live --out <フォルダ>`。
- 出力：`run2_recorded/outputs/A`・`B`。結果：`run2_recorded/results/`（`metrics_live.json`、`overlap_sheet_live.png`、`cmp_live.jpg`）。
- A は大きさの仮定（絵を撮ったカメラの高さ）が1回目 2.1m・2回目 1.62m と変わり、形も毎回変わった。B は2回とも図面に書いてある所は正確で、ずれたのは図面に無い所（右端の平屋のまわり、凹みの天井の素材）。

### 指示の原文との関係

- `prompts/A_image_only_prompt.md`・`B_image_plus_drawing_prompt.md`：1回目に渡した指示の原文そのまま（入力・出力の場所は `<KIT>`・`<WORKDIR>` と書いてあり、`prepare_run.py` が作業フォルダに置き換える）。
- `run2_recorded/prompts/A_prompt.md`・`B_prompt.md`：1回目と同じ文面に「Rhino で部分ごとに組む」を足しただけの、2回目の原文。入力・出力のフォルダは公開用に `<REC>/` と書き換えた。
- `prepare_run.py` は、原文から本文を取り出して場所を作業フォルダに置き換え、最後に「終わったら元の会話に戻るよう伝える」1文（模型の作り方には関係しない）を足して `prompt.md` にする。

### 再現しても同じにならない所

- AI の答えは毎回変わり、A の重なり率は回ごとに数ポイント動く。傾向（A は 70〜80% 前後、B は 90% 台）を見る。
- 図面づくりの往復（人の描き込み r1〜r9 と AI の書き出し v7〜v14）は人の判断そのもの。過程は Figma ボード（閲覧のみ）https://www.figma.com/board/Fajd8nO7JFtNX5Ty2JOus4 で見られる。B を同じ条件で試すなら `inputs/drawing_v14.png` をそのまま使う。
- 外観の絵は生成済みの画像を同梱（生成し直す手順は無い）。正解も図面どおりの模型なので、図面を渡した B に有利な比べ方。

## 10. 公開用に書いた物と、試していないこと

- `prompts/00_prepare_A.md`・`00_prepare_B.md`・`10_shoot_and_score.md`・`11_check_scoring.md` は公開用に書いた（実験者の AI が直接行った準備・撮影・採点を文章にした物）。
- 確かめたこと：`11_check_scoring` の採点の再計算（同じ値が出る）、`draw_v14.py` の図面の再現。
- 試していないこと：段 0〜4 を通しで流すこと、Claude Code・Codex で流すこと。`00_`・`10_` の指示はこの形では流していない。

失敗したら、試していない部分で起きた可能性を前提に、平易に伝えて次の手を提案してください。

## 11. 困った時（AI がすること）

| こんな時 | すること |
| --- | --- |
| Rhino を AI から動かせない | スクリプト形式で進める。撮影の時だけ `work/run_mine_here.py` をユーザーに ScriptEditor で実行してもらう。つなぎたいと言われたらセットアップ資料を案内 |
| 模型の壁が消える・形がおかしい | 面の向きが内向きの可能性。段 4 では面の向きだけ直してよい（寸法は変えない。実験でも A に3行足した） |
| 重なり率が急に低い（30% 台など） | 撮影中に Rhino の窓の大きさが変わった可能性。窓をそのままにしてもらい、撮影からやり直す |
| 模型づくりが途中で止まった | その会話で「続けてください」と入れてもらう。だめなら同じフォルダで新しい会話を始め、同じ1行 |
| 次の日に続きをやりたい | `work/progress.md` を読み、次に貼る1行を伝える |
| `C:/path/to/kit/` が見つからない | `run_compare.py`・`run_all_in_rhino.py`・`outputs/reference_v14.py` の先頭の仮の場所。キットの絶対パスに書き換える（自分の模型の撮影は `make_rhino_runner.py` が書き込むので不要） |
| 1回目の数値が公開値と最大 0.5 ポイント違う | 仕様（上の「Rhino なしで採点だけ確かめる」）。2回目の値で確かめる |

## 12. 外壁のテクスチャ

画像生成のサービス（ComfyUI のクラウド版）を使うので、費用がかかることを先に伝え、許可を取ってから行う。

- 比較に使った3種＋木：`tex/materials.json`（プロンプト・seed・物性値）を使い、ComfyUI（Qwen-Image 2.1 t2i）で色を生成 → `seam.py config` → `deepbump.py --config` → `make_pbr.py`（出力は `work/materials/`）→ `make_tex.py` で比較用に調整して `tex/` へ。詳しくは [skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md)。
- 外観に寄せたグレーの打放し `tex/concrete_v6_src/`：ComfyUI の Qwen-Image 2.1（画像編集、入力＝外観画像）で作った素地6枚、プロンプト原文（`PROMPTS.md`）、組み立てスクリプト `make_concrete_v6.py`。
  - `uv run --with pillow --with numpy python tex/concrete_v6_src/make_concrete_v6.py` で 14.4m 角・4096px のシームレスなテクスチャ（basecolor / normal / roughness / AO / height）を `tex/concrete_v6/` に作る（大きいのでリポジトリには入れていない）。
- プロンプトと seed が同じでも、クラウド側のモデル更新で絵は変わる。比較に使ったテクスチャは `tex/` に同梱。
- 生成物（`work/`）と DeepBump 本体（`tools/`）は `.gitignore` 済み。

## 13. そのほかに頼まれた時

- **図面を Figma で往復して作る**：[skills/figma-drawing-markup-loop.md](skills/figma-drawing-markup-loop.md)。人の描き込みが要るので、何をしてほしいかを1回ずつ具体的に頼む。
- **ユーザー自身の外観パースやスケッチから模型を起こす**：[skills/image-to-massing.md](skills/image-to-massing.md)。この場合は正解が無いので、採点はしない。仮定した寸法と確信度を一覧で返す。
- **テクスチャを作り直す**：上の「12. 外壁のテクスチャ」。
- 実験の公平さの決まり（A・B の分け方、採点、撮影の落とし穴）：[skills/input-comparison-experiment.md](skills/input-comparison-experiment.md)
