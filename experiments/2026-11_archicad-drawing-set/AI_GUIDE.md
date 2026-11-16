🇯🇵 日本語 | [🇺🇸 English](AI_GUIDE.en.md)

# AI_GUIDE：この実験を再現する AI エージェントへの手引き

あなた（AI エージェント）は、このフォルダ（以下 **キット**）を使って、建築家のユーザーと一緒に
「白紙の Archicad に家を組み、作図ルールに沿って図面8枚を描き、点検して直す」を再現します。
人向けの説明は [README.md](README.md) です。AI が知っておくこと（ファイル、コマンド、実験で実際にやったこと、困った時の対処）は、このファイルにまとめてあります。

家：架空の「打放しと水盤の家」（RC 2階建て、18,000 × 11,100、通り芯 X1〜X6 / Y1〜Y4）。

## 1. 基本の動き方

**手順の本体は `prompts/` の指示ファイルです。** ユーザーは各段で、新しい会話に次の形の1行を貼ります。
「`<指示ファイル>` を読んで、指示どおりに作業してください」
指示ファイルに書いてあることだけを行ってください。段の順番、保存、次に貼る1行は、ユーザーが [README.md](README.md) の表を見て進めます（指示ファイルには書いてありません）。
指示ファイルの名前が無いまま頼まれた時は、README の表を示して、どの段から始めるかをユーザーに確かめてください。

- **結果を作らないでください。** スクリプトが失敗したら、出力をそのまま見せて止まります。
- **Archicad への命令は、いつも1本ずつ。** 2つのスクリプトやエージェントから同時に送らないでください。
- 指示の中の「session_search、honcho、delegate は使わない」は、実験で使ったエージェント（Hermes Agent）の機能名。「記憶・過去の会話・ほかの AI への丸投げを使わない」と読み替えてください（その機能が無ければ無視してよい）。
- つながらない・Tapir が無い時は、セットアップ資料（日本語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja ／英語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en）を案内して止まります。

## 2. 段と指示ファイル

| 段（README の表） | ファイル | 中身 | 実験で |
| --- | --- | --- | --- |
| 0 | （人：Archicad で ファイル › 新規） | 空のプロジェクトを開く | 人が手で（cua-driver があれば「12」で AI が画面から） |
| 1 | `prompts/00_prepare.md` | `check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` を流すだけ | 追加（未使用） |
| 2 | `work/prompts/01_model_M.md` | 外形を組む | 同じ指示で実行 |
| 3 | `work/prompts/02_interior_I.md` | 間取りと通り芯（`work/grid.json`） | 同じ指示で実行 |
| 4 | `work/prompts/05_sections.md` | `make_sections.py create` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 5 | （人：断面の窓6つを1回ずつ開く） | S南・S東・S北・S西・A-A・B-B | 人が手で（cua-driver があれば「12」で AI が画面から） |
| 6 | `work/prompts/06_fix_model.md` | `fixA_snapshot` → `fixA_comps` → `fixA_walls` → `fixA_slabs --apply` → `fixA_found` → `fixA_raise` → `fixA_del2d --apply` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 7 | `work/prompts/12_sheet_SA` → `13_sheet_SB` → `14_sheet_ES` → `15_sheet_EN` → `16_sheet_EE` → `17_sheet_EW` → `10_sheet_P1` → `11_sheet_P2` | 1枚ずつ描く（1本ずつ新しい会話、1枚ごとに保存） | 同じ指示で実行（この順） |
| 8 | （人：断面記号の参照ID を A・B に） | ナビゲータで「S-01 A-A」「S-01 B-B」の名前を変更 | 人が手で（cua-driver があれば「12」で AI が画面から） |
| 9 | `work/prompts/18_export.md` | `layer_found.py` → `export_png.py` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 10 | `work/prompts/30_inspect_and_fix.md` | 点検、直しの指示を書く、直す | 追加（未使用） |
| 記録 | `03_south_elevation_recorded`・`04_fix_partition_F` | 実験の回の記録（ふだんの順では使わない） | 同じ指示で実行 |
| 記録 | `20_`〜`25_` | 実験の直しの記録（そのときの失敗に合わせた指示。あなたの結果には当てはまらないことが多い。形の例として使う） | 同じ指示で実行 |

- `work/prompts/` は段 1 の `prepare_workdir.py` が作ります。指示の中の `<KIT>`（作業フォルダ）・`<KITROOT>`（キット）・「port は 19723」は、ここで実際の値に置き換わります。キットの `prompts/` の元のファイルは書き換えません。
- スクリプトを流すだけの指示（`00_prepare`・`05_sections`・`06_fix_model`・`18_export`）は、下の「4. コマンドの順」を順に流して出力を見せるだけです。人が手で流しても同じです。

## 3. ファイルとスクリプト

- `README.md`・`README.en.md`：人（建築家）向け。`AI_GUIDE.md`・`AI_GUIDE.en.md`：このファイル
- `inputs/`
  - `rhino_house.py`：元にした家（Rhino のスクリプト、単位 mm）。AI は中の数字を読むだけで、Rhino は要らない。前の実験「[外観の絵だけ vs 絵＋図面](../2026-11_image-vs-drawing-3d/README.md)」と同じ家に、窓と仕上げを足した版
  - `rhino_house.jpg`：その見た目
  - `layout_1F.jpg`・`layout_2F.jpg`：間取りの図（架空。`02_interior_I` で使う）
- `prompts/`：上の表の指示ファイル
- `rules/`：作図ルール（立面・平面・断面）。描く AI は、これと Archicad から読める情報だけで描く
- `skills/`：AI エージェントに渡す知識（[skills/README.md](skills/README.md)、[Archicad 操作のコツ](skills/archicad-operation.md)、[点検と直しの指示の作り方](skills/inspection.md)）
- `results/`：実験の仕上がりの8枚（`1_P1`〜`8_EW`）、断面の直す前・後（`sa_before_after.jpg`）、作図ルールなし／ありの南立面（`noskill_vs_skill.jpg`。少し前の版の家）。**公開済みの結果なので上書きしない。**
- `images/`：README の画像
- `scripts/`：

| スクリプト | 役目 |
| --- | --- |
| `tapir_http.py` | Archicad の JSON API ＋ Tapir の命令を HTTP で送る最小のクライアント（MCP は使わない）。`default_port()` がポートを決める |
| `check_connection.py` | 接続の確認。`--scan` でポートを探して `work/archicad_port.txt` に書く、`--count` で白紙か数える、`--save` で保存 |
| `prepare_workdir.py` | `work/` を作り、`<KIT>`・`<KITROOT>`・ポートを置き換えた `work/prompts/` と `work/progress.md` を作る。`--with-grid` で記録の `grid.json` も入れる |
| `setup_stories.py <pln>` | 階を 1FL・2FL・RFL にして、指定の場所に保存 |
| `make_sections.py create` / `shoot` | `create`：立面用の線4本と断面 A-A・B-B の線を作る（`--aa-y`・`--bb-x`・`--margin`）。`shoot`：6面を画像に |
| `fixA_snapshot.py` | 直す前の壁の控えを `walls_before_fixA.json` に取る。`fixA_walls.py` より前に1回だけ（あれば止まる） |
| `fixA_comps.py` | 層のある部材（複合構造）を作る。材料は**番号**で選ぶ |
| `fixA_walls.py` | 外壁・間仕切りを層のある部材に替え、室内側の向きを合わせる |
| `fixA_slabs.py --apply` | 床・屋根の板を層のある部材に振り分ける（`--apply` 無しは計画の表示だけ）。材料名「コンクリート」 |
| `fixA_found.py` | 外壁の下に基礎（立上りと底盤）を足す。材料名「コンクリート」 |
| `fixA_raise.py [m]` | 家ごと上げる（既定 0.1）。敷地・水盤の板は元の高さに戻す。**2回流すと2回上がる** |
| `fixA_del2d.py --apply` | 前の回の 2D（線・文字）を消す（`--apply` 無しは表示だけ） |
| `layer_found.py` | 地中の部材を専用の画層へ移し、1階の外壁の下端を GL まで下げる。`hide`／`show` でその画層を隠す・出す。**2回流すと壁の下端が2回下がる** |
| `export_png.py` | 8枚を高解像度の PNG と文字に書き出す（立面・平面では地中の画層を自動で隠す）。出力は `<KITROOT>/out/` |
| `run_sheets.sh` | 段 7 の指示を1本ずつ新しいエージェントに渡し、1本ごとに保存（下の「5」） |
| `check_levels.py` | レベル表記の照合（`30_inspect_and_fix` が使う。実験では未使用） |
| `check_grid.py [path]` | 通り芯ファイルの確認と形の統一（既定 `work/grid.json`。`30_inspect_and_fix` が使う。実験では未使用） |
| `grid.json` | 実験で AI が間取りの回で決めた通り芯（記録） |
| `record/walls_before_fixA.json` | 実験のモデルの、直す前の壁の控え（記録。要素 ID はそのモデルだけの物で、ほかのモデルには使えない） |

必要な物：Python 3（ほとんど標準ライブラリだけ。`export_png.py` は Pillow と numpy、`prepare_workdir.py` は Pillow があれば本物の PNG を作る）、`run_sheets.sh` には bash（Windows なら Git Bash など）。

## 4. コマンドの順

キットのフォルダで、次の順です（「人」は Archicad の画面での操作、「指示」は新しい会話に1行）。

1. 人：空のプロジェクトを開く
2. `python scripts/check_connection.py --scan`
3. `python scripts/prepare_workdir.py`
4. `python scripts/setup_stories.py work/house_from_scratch.pln`
5. 指示 `01_model_M` → 保存 → 指示 `02_interior_I` → 保存
6. `python scripts/make_sections.py create`
7. 人：断面の窓6つを1回ずつ開く → 保存
8. `python scripts/fixA_snapshot.py` → `fixA_comps.py` → `fixA_walls.py` → `fixA_slabs.py --apply` → `fixA_found.py` → `fixA_raise.py` → `fixA_del2d.py --apply` → 保存
9. 指示 `12_`→`13_`→`14_`→`15_`→`16_`→`17_`→`10_`→`11_`（1本ずつ新しい会話。1本ごとに保存。`run_sheets.sh` でも同じ）
10. 人：断面記号の参照ID を A・B に → 保存
11. `python scripts/layer_found.py` → `python scripts/export_png.py`
12. 指示 `30_inspect_and_fix`（点検と直し。2〜3周で止める）

## 5. run_sheets.sh の使い方

段 7（や任意の指示）を、1本ずつ新しいプロセス（＝新しい会話）のエージェントに渡し、1本終わるごとに外から SaveProject を送ります。実験の連続実行と同じ形です。先に段 1 を済ませ、`work/prompts/` がある状態で、キットのフォルダから：

```
AGENT_CMD='claude -p --dangerously-skip-permissions' bash scripts/run_sheets.sh
AGENT_CMD='codex exec --full-auto' bash scripts/run_sheets.sh
SHEETS='12_sheet_SA 13_sheet_SB' AGENT_CMD='...' bash scripts/run_sheets.sh      # 一部だけ
SHEETS='20_fix_SA_round2' AGENT_CMD='...' bash scripts/run_sheets.sh             # 直しの指示も流せる
```

| 変数 | 意味 |
| --- | --- |
| `AGENT_CMD` | 必須。最後の引数に指示文を1つ受け取り、終わったら戻る非対話のコマンド。上の2つは例（実験で使ったのは Hermes Agent）。書き方は各エージェントの説明書で確かめる |
| `WORK` | 作業フォルダ（既定 `<KIT>/work`）。エージェントはここで起動し、「`prompts/<名前>.md` を読んで、指示どおりに作業してください。」を受け取る |
| `SHEETS` | 流す指示（`.md` を除いた名前）。既定は8枚を実験と同じ順（A-A → B-B → 南 → 北 → 東 → 西 → 1階 → 2階） |
| `MAX_SEC` | 1本の上限秒（既定 2400＝40分）。`timeout` コマンドが無ければ上限なし |
| `PY` | Python（既定 `python`） |

- 記録は `work/logs/<名前>.txt`。
- 保存に失敗したら（Archicad が落ちた可能性）止まります。
- 権限の確認を飛ばす設定は、作業フォルダと Archicad だけを触る前提で使います。

## 6. 自分のエージェントで指示を流す

指示ファイル（`prompts/*.md`、日本語）は、特定のエージェントに依存しない普通の文章です。エージェントを**キットのフォルダで**起動し、新しい会話に1行だけを入れます（最初の `prompts/00_prepare.md` だけキットの prompts、その後は `work/prompts/…`）。

- 1つの指示が終わってから次を入れる。指示ごとに新しい会話にすると、前の図の値を使い回さない（実験は1指示 = 1つの新しい会話。実験のエージェントは Hermes Agent）。
- 例：Claude Code はキットのフォルダで `claude` を起動して1行を入力。Codex は `codex` を起動して入力。まとめて流す時のコマンドは上の「5」。
- 操作のコツと点検の手順は `skills/` にある（エージェントへの渡し方は [skills/README.md](skills/README.md)）。

## 7. パスとポート

- 指示文の `<KIT>/` は作業フォルダ（指示が読むファイルを置いた場所）、`<KITROOT>/` はキットのフォルダ（`scripts/` がある所）。`python scripts/prepare_workdir.py` がキットの中に `work/` を作って置き換えまで済ませる（何度流してもよい。`grid.json`・`progress.md`・保存した `.pln` は消さない）。
- `prepare_workdir.py` を使わずに手で読み替える時は、`scripts/tapir_http.py`・`rules/*.md`・`inputs/` の中身を1つのフォルダの直下に置き、指示の `<KIT>/` をそのフォルダに置き換える。指示の `rhino_house.png`・`layout_1F.png` は、この公開版では `.jpg` なので、変換するか読み替える。
- スクリプトは、同じフォルダの `tapir_http.py`・`fixA_comps.json`・`walls_before_fixA.json` などを読み書きする（実行するとできる。`.gitignore` 済み）。書き出しは `<KITROOT>/out/`。
- ポート：環境変数 `ARCHICAD_PORT` → `work/archicad_port.txt`（`check_connection.py --scan` が書く）→ 19723 の順（`tapir_http.default_port()`）。`prepare_workdir.py` は、指示文の「port は 19723」をこの番号に置き換える。
- `work/progress.md`（進み具合のメモ）を使うのは `30_inspect_and_fix` だけ。

## 8. 実験で実際にやったこと

日付：2026年11月15〜16日。AI は Claude Opus 5.5（Hermes Agent で実行）。Archicad（日本語版・標準テンプレート）＋ Tapir（ポート 19723）。

| # | やったこと | 指示 |
| --- | --- | --- |
| 1 | 白紙の Archicad に、Rhino の家（スクリプトと画像）を読んで外壁・床・屋根・窓・扉を1つずつ組む | `01_model_M.md` |
| 2 | 間仕切り・内部の扉・階段・部屋を入れ、通り芯を1組決める（`grid.json`） | `02_interior_I.md` |
| 3 | 南立面を、作図ルールで線と塗りまで仕上げる（この時点の `rules/作図ルール_立面.md`。最後の「11/16 の点検で足した決まり」が入る前の版） | `03_south_elevation_recorded.md` |
| 4 | 残りの図面を描く。途中で、屋根を突き抜けた間仕切りを直し 2D を消して描き直した | `04_fix_partition_F.md` |
| 5 | 断面が弱かったので、実験者の AI がモデルを直す：壁の控え → `fixA_comps` → `fixA_walls` → `fixA_slabs` → `fixA_found` → 家ごと +0.1（`fixA_raise`）→ 保存 → 前の回の 2D を消す（`fixA_del2d`） | `scripts/` |
| 6 | 断面の作図ルールを新しく書き、8枚を1本ずつ新しい会話で描き直す（A-A → B-B → 南 → 北 → 東 → 西 → 1階 → 2階。1本ごとに外から SaveProject） | `12_sheet_SA.md` → … → `11_sheet_P2.md` |
| 7 | 書き出して点検。立面・平面に地中の線が出たので `layer_found.py` で画層を分けて書き出し直す | `scripts/` |
| 8 | 実務の図面の描き方（作法）と比べ、実験者の AI が直しの指示を書いて描く AI に入れる（3回目と4回目の間に、断面記号の参照ID を画面で A・B に変えた） | `20_`〜`25_`（例） |

- キットの段（README の表）は、この流れから 3・4 を除いた形。
- 実験の白紙のプロジェクトは、この家の前の回のモデルを別名で保存して中身を空にした物で、階（1FL・2FL・RFL）と断面・立面の線はその時の物を使った。キットでは同じ階を `setup_stories.py`、同じ線を `make_sections.py create` で作る（どちらも前の回に送った命令を取り出して一般化した物）。
- 8枚を続けて描いている間に Archicad が2回落ちた。対策として1枚ごとに保存し、指示で `GetElementsInDrawOrder` を使わないようにした。

### 指示の原文との照合

`01_`・`02_`・`03_`・`04_`・`10_`〜`17_`・`20_`〜`25_` は、実験で実際に渡した指示ファイルと1文字ずつ比べた。違いは次の3つだけ。
1. 実験のフォルダの場所（PC の中のパス）を `<KIT>/` に置き換えた（`prepare_workdir.py` が作業フォルダの場所に戻す）。
2. 冒頭の「Archicad」の後ろの版の番号を外した。
3. `20_`・`23_`・`24_` の「比べる相手」の一文を、一般的な言い方（「実務の図面の描き方（作法）と比べて」）に変えた。

スクリプトを流すだけの指示（`00_prepare`・`05_sections`・`06_fix_model`・`18_export`）は公開用に足した物。中身は、実験者の AI が直接流したスクリプトを同じ順・同じ引数で流し、出力を見せ、エラーなら止まる、だけ。`30_inspect_and_fix` は、実験者の AI が行った点検と直しの指示作りを文章にした物（実験では未使用）。

### 直しの回数

- 断面・立面：3回（2回目・3回目・4回目＝最後。西立面だけ2回）。例として A-A 断面の3回分を入れた（`20_`〜`22_`）。
- 平面：2回（2回目・最後）。1階は2回目が時間切れで途中で止まったので、やり直しを1回（`24_`）。例として1階平面の分を入れた（`23_`〜`25_`）。
- 直しの指示は、実験者の AI が図を画像と数値で点検して書き、そのまま描く AI に入れた（手順は [skills/inspection.md](skills/inspection.md)）。
- 実験者の AI が Archicad の画面で直接したこと：断面の印の名前を A / B に変えた、立面・平面の書き出しで地中（基礎）の画層を隠した、描く AI が足した小さい部屋の面積表示（かえって分かりにくくなった物）を外した。

### モデルの直し（段 6 の中身）

最初の断面は、屋根が厚さ約1mの塊、基礎なし、壁に層なしで、断面図として弱かった（`results/sa_before_after.jpg`）。

| 部位 | 直した後 |
| --- | --- |
| 外壁 | RC150 ＋ 断熱35 ＋ PB（室内側を部屋で判定して向きを決めた） |
| 間仕切り | PB12.5 ＋ LGS95 ＋ PB12.5 |
| 屋根 | 押えコン60 ＋ 断熱30 ＋ 防水10 ＋ RC200 の板に分け、天井と縁の壁（パラペット）を別に |
| 2階床 | フローリング15 ＋ 置床85 ＋ RC200 |
| 1階床 | フローリング15 ＋ 断熱85 ＋ RC土間150 ＋ 砕石100（車庫は土間コンクリート） |
| 基礎 | 外壁の下に立上りと底盤（底 GL-850） |
| 高さ | 全部の階を +100 上げて 1FL＝GL+100（敷地と水盤はそのまま） |

直した後の高さ（点検の照合に使う）：1FL＝GL+100、1CL＝GL+2850、2FL＝GL+3250、2CL＝GL+6600、軒高＝GL+6900、最高高さ＝GL+7600。

### 実験の結果に残っている弱い所

点検で見つけても、実験の図にもあった物です：車庫の壁が二重に見える（モデルに 0.3m 離れた壁が2枚ある）／1階平面にスラブの角の円弧が見える所がある／A-A 断面の梁の所に小さい白いすき間／X6 の基礎にすき間。寸法は 2D の線と文字で、モデルを変えても追従しない。

## 9. 公開用に変えたスクリプトと、試していないこと

| スクリプト | 出どころ |
| --- | --- |
| `fixA_comps.py`・`fixA_walls.py`・`fixA_found.py`・`tapir_http.py` | 実験で使った物（パスとポートだけ一般化） |
| `layer_found.py` | 実験で使った物に、あとから短いコマンドで行った「床・敷地・水盤も同じ画層へ」を足して1本に |
| `make_sections.py`・`export_png.py`・`setup_stories.py`・`fixA_del2d.py` | 実験の前後で使ったスクリプトを一般化（窓を ID でなく名前で探す、パス・撮影範囲を引数に。`fixA_del2d.py` の平面の部分は再構成） |
| `fixA_snapshot.py`・`fixA_raise.py` | 実験では短いコマンドで流した物を、記録から取り出してファイルにした（戻すスラブの選び方だけ ID から規則に） |
| `fixA_slabs.py` | 再構成。元は直すスラブを要素 ID で指定していた。同じ振り分けを高さと範囲の規則で行う（記録の値で同じ振り分けになることを確かめた） |
| `run_sheets.sh` | 実験の連続実行スクリプトを、どのエージェントでも使える形に |
| `check_connection.py`・`prepare_workdir.py`・`check_levels.py`・`check_grid.py` | 公開用に新しく書いた |

**試していないこと**
- 公開用に書き直したスクリプトは、文法の確認と、Archicad を使わない部分（作業フォルダ作り・計画の表示・文字の照合・通り芯ファイルの統一）の試し実行だけ。Archicad では流していない。
- `00_prepare`・`05_sections`・`06_fix_model`・`18_export`・`30_inspect_and_fix` の指示文は、この形では流していない。README の表の流れを、公開したキットで最初から最後まで通したことはまだない。
- 人が手で行う段（0・5・8）を AI の画面操作で行う流れ（「12」）も、Claude Code・Codex では通しで試していない。

失敗したら、試していない部分で起きた可能性を前提に、出力をそのまま見せて止まり、どこまで進んだかをユーザーと確かめてください。

## 10. 困った時（AI がすること）

| こんな時 | すること |
| --- | --- |
| 接続できない、ポートが違う | Archicad が起動してプロジェクトが開いているかをユーザーに確かめてもらい、`check_connection.py --scan` をもう一度。だめならセットアップ資料を案内して止まる |
| 材料が見つからない・違う材料になる | テンプレートが日本語の標準でない。`fixA_comps.py` は材料を**番号**で、`fixA_found.py`・`fixA_slabs.py` は名前「コンクリート」で選ぶ。ユーザーの許可を取り、各スクリプト先頭の番号・名前を、そのテンプレートの材料に合わせて書き換える |
| 断面の窓を開けない（ChangeWindow が失敗） | 版によっては、作ったばかりの断面の窓を AI から開けない。段 5（人が画面で6つを1回ずつ開く）を済ませたか確かめてもらう。cua-driver につながっていれば「12」の段 5 で開ける |
| 断面記号の参照ID を変えたい | Archicad への命令（JSON API・Tapir）からは変えられない。段 8 をユーザーに頼むか、cua-driver につながっていれば「12」の段 8 で画面から変える |
| Archicad が落ちた | ユーザーに `work` の「house_from_scratch」を開き直してもらう（復元は「いいえ」）。最後に保存した所から続ける。続けて描く時は1枚ごとに保存し、`GetElementsInDrawOrder` を使わない |
| スクリプトが途中で失敗した | 流し直す前に、どこまで反映されたかを確かめる。`fixA_raise.py`（2回流すと2回上がる）と `layer_found.py`（壁の下端が2回下がる）は流し直さない |
| `fixA_snapshot.py` が「既にある」で止まる | 前の控えを残すのが正しい。`fixA_walls.py` 以降を流した後は取り直さない（`--force` は、まだ直しを始めていない時だけ） |
| 指示が `rhino_house.png` などを見つけられない | 公開版は `.jpg`。読み替えるか変換する |
| 書き出しの立面・平面に地中の線が出る | `layer_found.py` を流したか確かめる（`layer_found.py hide` で隠せる） |
| 点検で、実験の図にもあった弱い所が出た | 上の「実験の結果に残っている弱い所」。直すかどうかはユーザーと決める |

## 11. 参考

- 操作のコツ（落ちない送り方、命令の書き方）：[skills/archicad-operation.md](skills/archicad-operation.md)
- 点検と直しの指示の作り方：[skills/inspection.md](skills/inspection.md)
- スキル（rules・skills）のエージェントへの渡し方：[skills/README.md](skills/README.md)
- 作図ルール：[rules/README.md](rules/README.md)

## 12. cua-driver で人の段を AI に任せる

段 0・5・8 は Archicad への命令（JSON API・Tapir）ではできないので、画面を操作して行います。その道具が **cua-driver**（[trycua/cua](https://github.com/trycua/cua)。アプリの窓を読み取り、クリック・入力をする MCP サーバー）です。

- cua-driver そのものは、実験者の AI エージェント（Hermes Agent）で動くことを確かめています。**Claude Code・Codex から、この「12」の手順で段 0・5・8 を行うことは、まだ通しで試していません。** うまくいかなければ、出力と画面の状態をそのまま見せて止まり、その段をユーザーに手で頼んでください。
- 下のコマンドは cua の公式の説明（2026年11月時点）から取った物です。コマンドや道具の名前は版で変わることがあります。違っていたら、その時の公式の説明を優先してください。

### 12.1 入れる・つなぐ（ユーザーの了承を得てから）

入れる物はユーザーのパソコン全体に入り、AI の設定（MCP の登録）も書き換えます。**流す前に、何を入れるかをユーザーに伝えて了承を得てください。** 管理者の権限は要りません。どちらも、ユーザーがふだん使っている画面（ログインしているデスクトップ）の端末で流します（SSH やサービスからではなく）。

Windows（PowerShell）：

```
irm https://cua.ai/driver/install.ps1 | iex
cua-driver autostart kick
```

`autostart kick` は、サインイン時に起動する登録をすぐ動かします。登録できなかった時は、別の端末で `cua-driver serve` を流し、その端末を開いたままにします。

macOS（ターミナル）：

```
/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"
cua-driver permissions grant
```

`permissions grant` で、macOS が「アクセシビリティ」と「画面収録とシステムオーディオ録音」の許可を求めます。**システム設定のスイッチは、ユーザー本人が入れます。AI は押しません**（cua-driver も、この種の確認画面への入力は既定で拒みます）。後で `cua-driver permissions status` で確かめられます。

AI へのつなぎ：入れる時のスクリプトが `cua-driver connect` を流し、入っている Claude Code・Codex に自動でつなぎます（サーバー名は `cua-driver`）。後から入れた時や、つながっていない時は：

| エージェント | コマンド | 手で登録する形（`cua-driver mcp-config --client …` が、そのパソコンの実際のパスで表示する） |
| --- | --- | --- |
| Claude Code | `cua-driver connect --client claude` | `claude mcp add-json --scope user cua-driver '{"command":"<cua-driver のパス>","args":["mcp"]}'` |
| Codex（CLI・アプリ・IDE） | `cua-driver connect --client codex` | `codex mcp add cua-driver -- <cua-driver のパス> mcp`（`~/.codex/config.toml` の `[mcp_servers.cua-driver]` に `command` と `args = ["mcp"]`） |

- `--dry-run` を付けると、変えずに中身だけ見られます。何度流しても同じ結果です。
- つないだ後は、エージェントを一度終了して起動し直します（ユーザーに頼む）。
- `<cua-driver のパス>` は、macOS は `command -v cua-driver`、Windows は PowerShell で `(Get-Command cua-driver).Source`。

出典：
- cua-driver の入れ方と確かめ方：https://cua.ai/docs/cua-driver/quickstart
- エージェントへのつなぎ方：https://cua.ai/docs/cua-driver/guides/connect-your-agent 、https://cua.ai/docs/cua-driver/guides/claude-code 、https://cua.ai/docs/cua-driver/guides/codex
- 権限のモード：https://cua.ai/docs/cua-driver/guides/permissions
- Claude Code の MCP：https://code.claude.com/docs/en/mcp
- Codex の MCP：https://developers.openai.com/codex/mcp

### 12.2 確かめる

```
cua-driver status          # 「Cua Driver daemon is running」と出る
cua-driver doctor          # 警告も全部読む（終了コード 0 だけでは足りない）
cua-driver call list_apps  # 開いているアプリが並ぶ。空なら画面に届いていない
claude mcp list            # Claude Code：cua-driver がある（会話の中では /mcp）
codex mcp list             # Codex：cua-driver がある
```

起動し直した新しい会話で、cua-driver の道具（`list_apps` など）が使えるかを1回呼んで確かめます。公式の最初の練習は「電卓で 6 × 7 を計算し、画面の表示 42 を読み返す」です。

### 12.3 使う道具

| 道具 | 使い方 |
| --- | --- |
| `list_apps`・`list_windows` | Archicad の pid と窓を見つける |
| `get_window_state` | 窓の部品の一覧（番号つき）と画面の画像を取る。**操作の前と後に毎回取り直す**（前の番号は使い回せない） |
| `click`・`double_click`・`right_click` | 部品の番号か、窓の中の座標でクリック |
| `invoke_menu` | メニューを名前の順にたどって実行する（例：ファイル › 新規） |
| `type_text`・`press_key`・`hotkey` | 文字の入力、Enter・Esc、Ctrl+A など |
| `zoom` | 窓の一部を拡大して読む（ナビゲータの小さい文字など） |
| `bring_to_front` | 裏からの操作が効かない時に、Archicad を前に出す |

道具の一覧は `cua-driver list-tools` で見られます。

### 12.4 段ごとの手順

共通の決まり：
- 触るのは Archicad の窓だけ。ほかのアプリ、OS の確認画面、ほかのプロジェクトのファイルは触らない。
- 1回操作したら `get_window_state` を取り直し、思ったとおりに変わったかを確かめてから次へ。違っていたら止めて、画面の状態をユーザーに見せる。
- メニューやダイアログの文字は Archicad の言語で違う（日本語版：ファイル › 新規、英語版：File › New）。画面に出ている文字を読んで選ぶ。
- 「保存しますか」などの思っていなかったダイアログが出たら、押さずにユーザーに聞く。
- この間、Tapir の命令（スクリプト）を同時に送らない。ユーザーにはマウスとキーボードに触らないよう伝える。
- 保存はユーザーが Archicad で行うか、ユーザーの了承を得て `python scripts/check_connection.py --save`。

**段 0：空のプロジェクトを開く**
1. `list_apps` で Archicad が起動しているか見る。起動していなければ、ユーザーに起動してもらう（ユーザーが頼んだ時だけ `launch_app`）。
2. `get_window_state` → `invoke_menu` で ファイル › 新規（効かなければメニューを `click` でたどる）。
3. 新規のダイアログが出たら、画面を読んで、既定のテンプレートのまま新しいプロジェクトを作る項目を選び、新規（OK）を押す。前のプロジェクトの保存を聞かれたら、ユーザーに聞く。
4. 確かめ：`get_window_state` で、題名が新しい名称未設定のプロジェクトになったか見る。続けて `python scripts/check_connection.py --scan` → `--count` で、壁・スラブなどが 0 か見る。

**段 5：断面の窓6つを1回ずつ開く**
1. `get_window_state` でナビゲータを探す（無ければ、ウィンドウ › パレット からナビゲータを出す）。プロジェクト一覧を選び、断面図の項目を開く（左の三角を `click`）。
2. S南・S東・S北・S西・A-A・B-B の6つ（「S-01 A-A」のように番号つきで出ることがある）を、1つずつ `double_click`。
3. 1つ開くごとに `get_window_state` を取り直し、その断面の窓（タブ）が開いたか確かめる。開くとナビゲータの表示が変わることがあるので、次の項目は取り直した一覧から探す。
4. 6つ開いたら、ユーザーに保存を頼む（または了承を得て `--save`）。

**段 8：断面記号の参照ID を A・B に**
1. ナビゲータの断面図で「S-01 A-A」を `right_click` → 出たメニューを `get_window_state` で読み、断面図の名前を変更する項目（日本語版「断面図の名前を変更...」）を `click`。
2. ダイアログの参照ID の欄を `click` → `hotkey`（Windows は Ctrl+A、macOS は Cmd+A）で中身を選ぶ → `type_text` で `A` → OK。名前の欄は変えない。
3. `get_window_state` で、ナビゲータの表示が A になったか確かめる。
4. 「S-01 B-B」も同じく `B` に。終わったら保存（段 5 と同じ）。

### 12.5 安全のために

- cua-driver の既定（standard）は、**どのアプリにも入力できる**モードです。この段の間だけ使い、ほかの作業を同じ会話で頼まない。範囲を絞るなら、公式の「Permissions」にある bounded モード（使ってよい道具とアプリを書いた設定ファイル）を使う。
- エージェントの確認（Claude Code の許可、Codex の承認）は飛ばさない。`run_sheets.sh` で使う「確認を飛ばす」設定は、この段では使わない。
- cua-driver は、中身を含まない利用状況を既定で送ります。止めるなら `cua-driver telemetry disable`。
- 使い終わって止めたい時は `cua-driver stop`。
