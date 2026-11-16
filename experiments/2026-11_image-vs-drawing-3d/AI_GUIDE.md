🇯🇵 日本語 | [🇺🇸 English](AI_GUIDE.en.md)

# AI_GUIDE：この実験を再現する AI エージェントへの索引

あなた（AI エージェント）は、このフォルダ（以下 **キット**）を使って、建築家のユーザーと一緒に
「外観の絵1枚だけ（A）／絵＋図面（B）で AI に Rhino 模型を作らせ、正解の模型との重なり率で比べる」を再現します。

**手順の本体は `prompts/` の指示ファイルです。** ユーザーは各段で、次の形の1行を貼ります。
「`<指示ファイル>` を読んで、指示どおりに作業してください」
指示ファイルの名前が無いまま頼まれた時は、下の表で今どの段かを判断し（`work/progress.md` があれば読む）、その段の指示ファイルを読んで進めてください。

## いちばん大事な決まり：キットを開いているあなたは模型を作らない

キットには正解が入っています（`outputs/reference_v14.py`、`scripts/draw_v14.py`、`outputs/`、`run2_recorded/outputs/`、`results/`）。
A・B の模型は、入力だけを入れた別のフォルダ（`ai-run-A`・`ai-run-B`）で、**新しい会話の AI** が作ります。あなたの役目は、準備・撮影・採点・説明です。正解の中身（寸法など）を、ユーザーや模型を作る AI に伝えないでください。

## 段と指示ファイル

| 段 | 作業フォルダ | ユーザーが貼る1行の中のファイル | 中身 |
| --- | --- | --- | --- |
| 0 | キット | `prompts/00_prepare_A.md` | 形式（Rhino で組む／スクリプトだけ）を決め、`prepare_run.py A` で `../ai-run-A` を作る |
| 1 | ai-run-A（新しい会話） | `prompt.md` | 模型を作る（実験の指示の原文。キットの AI は関わらない） |
| 2 | キット | `prompts/00_prepare_B.md` | `../ai-run-B` を作る |
| 3 | ai-run-B（新しい会話） | `prompt.md` | 模型を作る |
| 4 | キット | `prompts/10_shoot_and_score.md` | 模型を `work/mine/` に集め、`make_rhino_runner.py` → Rhino で撮影 → `metrics.py --out work/results_mine` |
| — | キット | `prompts/11_check_scoring.md` | Rhino 無しで、同梱の影絵から録画回の数値を再計算（`metrics_live.py --out work/results_check`） |

## どの段でも守る決まり

1. **ユーザーは建築家で、プログラマーではない。** 返事はユーザーと同じ言語で、建築の言葉で短く。コマンド、パス、プログラム用語（JSON、IoU、Python、MCP など）を見せない（IoU →「重なり率」）。
2. **コマンドは全部あなたが実行する。** Python や画像処理の道具を入れる時は、先に許可を取る。
3. **人に頼むのは、新しい会話を始めることと、Rhino の画面に関わる操作だけ。** 何をどこに貼るかまで具体的に書く。
4. **Rhino に命令を送るのは、いつも1つの AI だけ。** 模型を作る会話が Rhino を使っている間は、あなたは Rhino に何も送らない。
5. **公開済みの結果（`results/`・`run2_recorded/results/`・`outputs/`）を上書きしない。** あなたの結果は `work/` に。
6. **結果を作らない。** 失敗したら平易に伝え、次の手を提案する。
7. つながらない時は、セットアップ資料（日本語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja ／英語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en）を案内する。
8. 指示文にある `vision_analyze`（画像を見る）・`execute_rhino_code`（Rhino で Python を実行）は、実験で使ったエージェント（Hermes Agent）のツール名。ほかのエージェントでは、同じ働きのツールに読み替える。

## そのほかに頼まれた時

- **テクスチャ（外壁の質感）を作り直す**：[skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md) と TECHNICAL.md の「外壁のテクスチャ」。画像生成のサービス（ComfyUI のクラウド版）を使うので、費用がかかることを先に伝え、許可を取る。
- **図面を Figma で往復して作る**：[skills/figma-drawing-markup-loop.md](skills/figma-drawing-markup-loop.md)。人の描き込みが要るので、何をしてほしいかを1回ずつ具体的に頼む。
- **ユーザー自身の外観パースやスケッチから模型を起こす**：[skills/image-to-massing.md](skills/image-to-massing.md)。この場合は正解が無いので、採点はしない。仮定した寸法と確信度を一覧で返す。
- 実験の公平さの決まり（A・B の分け方、採点、撮影の落とし穴）：[skills/input-comparison-experiment.md](skills/input-comparison-experiment.md)
- ファイルの一覧と細部：[TECHNICAL.md](TECHNICAL.md)
