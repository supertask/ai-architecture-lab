# AI_GUIDE：この実験を再現する AI エージェントへの手順書

あなた（AI エージェント）は、このフォルダ（以下 `<KIT>`）を使って、建築家のユーザーと一緒に
「外観の絵1枚だけ（A）／絵＋図面（B）で AI に Rhino 模型を作らせ、正解の模型との重なり率で比べる」を再現します。
ユーザー向けの説明は [README.md](README.md)、ファイルの一覧と細部は [TECHNICAL.md](TECHNICAL.md) にあります。

## いちばん大事な決まり：あなたは模型を作らない

`<KIT>` には正解が入っています（`outputs/reference_v14.py`、`scripts/draw_v14.py`、`outputs/`、`run2_recorded/outputs/`、`results/`）。
このガイドを読んでいるあなたは答えを見られる立場なので、**A・B の模型を自分で作ってはいけません**。
模型は、入力だけを入れた別のフォルダで、**新しい会話の AI** に作らせます。あなたの役目は、準備・撮影・採点・説明です。
正解のファイルの中身（寸法など）を、ユーザーや模型を作る AI に伝えないでください。

ユーザーの言葉と、あなたの仕事：

| ユーザーの言葉 | 段階 |
| --- | --- |
| 「このフォルダの AI_GUIDE.md を読んで、絵だけの場合（A）の実験を準備して」 | 段階0 → 段階1（A） |
| 「絵と図面の場合（B）の実験を準備して」 | 段階1（B） |
| （新しい会話で）「prompt.md を読んで、その指示どおりに作業してください」 | あなたではなく、別の会話の AI がやる |
| 「A と B の模型ができた。正解と同じ条件で撮って、重なり具合を採点して」 | 段階2 |
| 「Rhino を使わずに、採点のしかただけ確かめて」 | 段階3 |

## ユーザーとの約束（必ず守る）

1. **ユーザーは建築家で、プログラマーではない。** コマンド、パス、プログラム用語（JSON、IoU、Python、MCP など）を返事に出さない。要る時はひとことで言い換える（例：IoU →「重なり率」）。
2. **コマンドは全部あなたが実行する。** ユーザーに実行を頼まない。Python の用意も自分で行う（入れる時はユーザーに許可を取る）。
3. **進み具合を短く伝える。** 区切りごとに1〜3行。
4. **人に頼むのは、新しい会話を始めることと、Rhino の画面に関わる操作だけ。** 何をどこに貼るかまで具体的に書く。
5. **Rhino に命令を送るのは、いつも1つの AI だけ。** 模型を作る会話が Rhino を使っている間（`--live` の形式）は、あなたは Rhino に何も送らない。
6. **結果を作らない。** 失敗したら平易に伝え、次の手を提案する。

## 段階0：準備の確認（最初に1回）

1. **Python があるか**：`python --version`（無ければ `python3`、`py -3`）。`uv` があれば、画像処理は `uv run -q --with pillow --with numpy python ...` で動かせる。無ければ `pip install pillow numpy`（許可を取ってから）。
2. **AI から Rhino を動かせるか**：あなたの道具の中に、Rhino の中で Python を実行するもの（例：`execute_rhino_code`）があり、Rhino が起動しているか。
   - あれば：模型づくりは「Rhino で部分ごとに組む」形式（`--live`、録画した回と同じ）を勧める。撮影もあなたが Rhino に送れる。
   - 無ければ：「スクリプトを書くだけ」の形式（1回目と同じ）で進められる。撮影の時だけ、ユーザーに「Rhino で、このフォルダの scripts の中の run_all_in_rhino.py を開いて実行してください（ScriptEditor）」と頼む。
     接続を入れたいと言われたら、セットアップ資料 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T を案内する（この資料のプロンプトを AI に貼ると、AI が接続を入れる）。

## 段階1：A（または B）の準備

1. `<KIT>` の**外**に、入力だけのフォルダを作る。場所は `<KIT>` の1つ上のフォルダに `ai-run-A`（B なら `ai-run-B`）を既定にする。
   ```
   python scripts/prepare_run.py A --out <KIT の1つ上>/ai-run-A          # スクリプトを書くだけの形式
   python scripts/prepare_run.py A --live --out <KIT の1つ上>/ai-run-A   # Rhino で部分ごとに組む形式
   ```
   （`prepare_run.py` はキットの中に作ろうとすると止まる。）
2. できたフォルダに、外観の絵（B なら図面も）と `prompt.md` だけがあるかを確かめる。
3. ユーザーにこう伝えて止まる（フォルダの場所は、エクスプローラーで探せる書き方で）：
   > 準備ができました。模型を作る AI が正解を見ないように、別のフォルダ「ai-run-A」（このフォルダと同じ場所）を作りました。
   > アプリで**新しい会話**を始め、作業するフォルダとして「ai-run-A」を選んで、次の文を貼ってください。
   > 「prompt.md を読んで、その指示どおりに作業してください」
   > 15〜40分ほどかかります。終わったら、この会話に戻って教えてください。
   - B は A と別の新しい会話で、同じ AI で行うよう添える。
   - 新しい会話には、このキットの話や、過去の会話・メモリ・スキルを持ち込まないよう添える（条件が変わるため）。
4. 指示文の中の `vision_analyze`（画像を見る）・`execute_rhino_code`（Rhino で Python を実行）は、実験で使ったエージェントのツール名。ほかのエージェントでも同じ働きのツールが使われるので、そのままでよい。

## 段階2：撮影と採点（「A と B の模型ができた。撮って、採点して」）

1. 模型を作った会話の出力を確かめる：スクリプト形式は `ai-run-A/outputs/A/model.py`、`--live` は `ai-run-A/A_out/model.py`（B も同様）。`params.json`・`notes.md` もあるか。
   無い・途中で止まっている時は、ユーザーに平易に伝え、新しい会話でもう一度頼むよう勧める。
2. **公開済みの結果を上書きしない。** `results/`・`run2_recorded/results/`・`outputs/` は元のまま残す。ユーザーの模型は `<KIT>/work/mine/A/model.py`・`work/mine/B/model.py` にコピーして使う。
3. **撮る**（Rhino で。窓の大きさを変えない）：
   - `outputs/reference_v14.py` は `run_compare.py` 経由なら `KIT_OVERRIDE` が効くので書き換えなくてよい（単独で動かす時だけ、先頭の `KIT` を実際の場所に。TECHNICAL.md の「パスについて」）。
   - `scripts/run_compare.py` の `KIT_OVERRIDE` の仕組みを使う（`run_all_in_rhino.py` と同じく `g = {'KIT_OVERRIDE': KIT}` で読み込み、`run` を取り出す）。`KIT` は `<KIT>` の実際の場所（末尾 `/`）。
   - 正解とユーザーの A・B を、**同じ Rhino の窓の状態で、続けて**撮る（正解の影絵も撮り直す。同梱の影絵は別の窓の大きさで撮った物なので混ぜない）：
     - `run(KIT + 'outputs/reference_v14.py', 'C_reference_v14', False, WALLS)`
     - `run(KIT + 'work/mine/A/model.py', 'A_image_only', True, WALLS)`（A は原点が無いので左端・最前にそろえる）
     - `run(KIT + 'work/mine/B/model.py', 'B_image_plus_drawing', False, WALLS)`
     - `WALLS = ('concrete', 'black_mortar', 'rammed_earth')`
   - 出力は `work/compare/<名前>/`（`sil_*.png`・`eye_*.png`・`model.3dm`）。
   - Rhino に送れない時は、上の3行だけを書いた小さなスクリプトを `work/` に作り、ユーザーに「Rhino でこのファイルを開いて実行してください」と頼む（ScriptEditor）。撮影中は Rhino の窓の大きさを変えないよう添える。
4. **模型が立体になっているかを画像で確かめる**（`eye_*.png`）。壁が消えている時は、面の向きが内向きの可能性がある。実行上の不具合だけを直し（`if brep.SolidOrientation == G.BrepSolidOrientation.Inward: brep.Flip()`）、寸法は変えず、直したことをユーザーに伝える（実験でも A で同じ直しをした）。
5. **採点**：`scripts/metrics.py` を同じ `scripts/` の中に `metrics_mine.py` としてコピーし（`fontutil.py` を読むので同じ場所に置く）、出力先 `RES` を `os.path.join(HERE, '..', 'work', 'results_mine') + '/'` に変えて（フォルダも作る）、`uv run -q --with pillow --with numpy python scripts/metrics_mine.py <KIT>/work/compare` で実行する（元の `results/` を上書きしないため）。A だけ・B だけの時は、コピーの `TAGS` をその分だけにする。
6. **ユーザーに報告する**：
   - 4方向（真上・正面・右側面・裏）の重なり率を表で。公開した値（A 68〜80%、B 96〜100%。スクリプト形式の回は A 77〜80%、B 91〜99%）と並べる。
   - AI が仮定した寸法のうち効いた物（`params.json` の確信度の低い物。A ならカメラの高さなど）を2〜3行で。
   - 比較の画像の場所（「このフォルダの work の中の results_mine」）。
   - 数字が急に低い（30% 台など）時は、まず撮影の縮尺（窓の大きさ）を疑い、影絵を並べて大きさを確かめてから伝える。

## 段階3：Rhino を使わずに採点のしかただけ確かめる

1. 採点のスクリプトを、Rhino で撮った影絵の代わりに同梱の影絵（`results/silhouettes/`）で動かす：`uv run -q --with pillow --with numpy python scripts/metrics_live_check.py results/silhouettes`（下の注意どおりにコピーした物）
   - そのまま実行すると `run2_recorded/results/` を書き直す（値は同じになるはずだが、公開した物は残したい）。`metrics_live.py` を同じ `scripts/` の中に `metrics_live_check.py` としてコピーし、出力先 `RES` を `work/results_check/` に変えて（フォルダも作る）から、そちらを実行する。
2. 出た値が `run2_recorded/results/metrics_live.json`（録画した回：真上 A 68%／B 100%、正面 76%／99%、右側面 80%／97%、裏 76%／96%）と同じかを確かめ、ユーザーに表で伝える。
3. 採点のしかたを平易に説明する：「正解と AI の模型を同じ向きから影絵で撮り、重なった面積を、どちらかが占める面積で割っています。位置のずれは ±3m の範囲で一番重なる所に合わせてから測っています」。

## そのほかに頼まれた時

- **テクスチャ（外壁の質感）を作り直す**：[skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md) と TECHNICAL.md の「外壁のテクスチャ」。画像生成のサービス（ComfyUI のクラウド版）を使うので、費用がかかることを先に伝え、許可を取る。
- **図面を Figma で往復して作る**：[skills/figma-drawing-markup-loop.md](skills/figma-drawing-markup-loop.md)。人の描き込みが要るので、何をしてほしいかを1回ずつ具体的に頼む。
- **ユーザー自身の外観パースやスケッチから模型を起こす**：[skills/image-to-massing.md](skills/image-to-massing.md)。この場合は正解が無いので、採点はしない。仮定した寸法と確信度を一覧で返す。
- 実験の公平さの決まり（A・B の分け方、採点、撮影の落とし穴）：[skills/input-comparison-experiment.md](skills/input-comparison-experiment.md)
