# 10 撮影と採点：正解・A・B を同じ条件で撮り、重なり率を出す

この指示は公開キット用に新しく書いたものです（実験では、実験者の AI エージェントが `scripts/run_all_in_rhino.py` と `scripts/metrics*.py` と同じ処理を直接行いました）。
**キット**＝このファイルがある `prompts` フォルダの1つ上のフォルダです。コマンドはキットのフォルダで実行します。

## 決まり
- あなたは模型を作らない・直さない（例外は下の手順4の「面の向き」だけ）。正解の中身をユーザーに伝えない。
- 返事はユーザーと同じ言語で、建築の言葉で短く。コマンド・パス・プログラム用語は見せない（IoU →「重なり率」）。コマンドは全部あなたが実行する。結果を作らない。
- Rhino に命令を送るのは、いつも1つの AI だけ。模型を作る会話がまだ Rhino を使っているなら、終わるまで待つ。
- 公開済みの結果（`results/`・`run2_recorded/results/`・`outputs/`）は上書きしない。あなたの結果は `work/` に書く。

## 手順
1. **できた模型を集める**：`work/progress.md` で A・B のフォルダの場所と形式を確かめ（無ければキットの1つ上の `ai-run-A`・`ai-run-B`）、
   - スクリプト形式：`ai-run-A/outputs/A/model.py`、live 形式：`ai-run-A/A_out/model.py`（B も同様）。`params.json`・`notes.md` もあるか。
   - `work/mine/A/model.py`・`work/mine/B/model.py` にコピーする（`params.json`・`notes.md` も同じフォルダへ）。
   - 無い・途中で止まっている時は、ユーザーに平易に伝え、その会話に「続けてください」と送るか、新しい会話で同じ1行をもう一度貼るよう勧めて止まる（片方だけで進めてよいと言われたら、ある方だけで進める）。
2. **撮影用のファイルを作る**：`python scripts/make_rhino_runner.py` → `work/run_mine_here.py`（正解と、あなたの A・B を撮る）。
3. **撮る**（5〜10分。Rhino の窓の大きさを途中で変えない）：
   - あなたが Rhino 接続を使える時：`work/run_mine_here.py` の中身を、その「Python を実行する」ツールにそのまま送る。最初に、ユーザーに「これから Rhino で撮影します。終わるまで Rhino の窓の大きさを変えたり、画面を触ったりしないでください」と伝える。
   - 使えない時：ユーザーにこう頼んで待つ：
     > Rhino で、コマンド「ScriptEditor」を実行し、開いた画面の「開く」で、このフォルダの中の work フォルダにある「run_mine_here.py」を開いて、実行ボタン（▶）を押してください。終わるまで5〜10分、Rhino の窓の大きさを変えないでください。終わったら「できた」と送ってください。
   - 撮れたかを確かめる：`work/compare/C_reference_v14/`・`A_image_only/`・`B_image_plus_drawing/` に `sil_top.png` などがあるか。
4. **模型が立体になっているか**を `work/compare/*/eye_concrete.png` で見る。壁が消えている時は、面の向きが内向きの可能性がある。実行上の不具合だけを直し（ソリッドを作った所に `if brep.SolidOrientation == G.BrepSolidOrientation.Inward: brep.Flip()`）、寸法は変えず、直したことをユーザーに伝えて手順2〜3をやり直す（実験でも A で同じ直しをした）。
5. **採点**（数分）：`uv run -q --with pillow --with numpy python scripts/metrics.py work/compare --out work/results_mine`
   （`uv` が無ければ Pillow と numpy を入れた Python で。A だけ・B だけの時は `--tags A_image_only` などを足す）
   → `work/results_mine/metrics.json` と `overlap_sheet.png`。
6. **数字を確かめる**：急に低い（30% 台など）時は、まず撮影の縮尺（窓の大きさ）を疑い、影絵を並べて大きさを確かめてから伝える。
7. `work/progress.md` に1行足す。
8. **ユーザーに報告して止まる**：
   - 4方向（真上・正面・右側面・裏）の重なり率を表で。公開した値（録画した回：A 68〜80%、B 96〜100%。スクリプト形式の回：A 77〜80%、B 91〜99%）と並べる。
   - AI が仮定した寸法のうち効いた物（`params.json` の確信度の低い物。A ならカメラの高さなど）を2〜3行で。
   - 比較の画像の場所（「このフォルダの work の中の results_mine」）。
   - 採点のしかたをひとことで：「正解と AI の模型を同じ向きから影絵で撮り、重なった面積を、どちらかが占める面積で割っています。位置のずれは ±3m の範囲で一番重なる所に合わせてから測っています」。
