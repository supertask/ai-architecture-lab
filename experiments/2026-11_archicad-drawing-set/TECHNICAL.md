🇯🇵 日本語 | [🇺🇸 English](TECHNICAL.en.md)

# 技術メモ：白紙の Archicad から図面8枚まで（詳しい人向け）

建築家向けの説明は [README.md](README.md)、AI 向けの索引は [AI_GUIDE.md](AI_GUIDE.md)、各段の手順は [prompts/](prompts/) にあります。
ここには、ファイルの一覧・実験でやった順・モデルの直しの中身・スクリプトの出どころ・パスの扱いをまとめています。

家：架空の「打放しと水盤の家」（RC 2階建て、18,000 × 11,100、通り芯 X1〜X6 / Y1〜Y4）。

## 動かすのに要るもの

- Archicad（日本語版で実験。テンプレートの材料名「コンクリート」などを使うスクリプトがある）と Tapir アドオン
  - Tapir は Archicad の JSON API に命令を足すアドオン。キットは Python から HTTP（ポート 19723）で命令を送るだけで、MCP は使わない。Python を書いて実行できる AI エージェントなら、どれでも動かせる。
- Python 3（標準ライブラリだけで動く物が多い。`export_png.py` は Pillow と numpy、`prepare_workdir.py` は Pillow があれば本物の PNG にする）
- Archicad のテンプレートは日本語の標準。`fixA_comps.py` は材料（ビルディングマテリアル）を**番号**で、`fixA_found.py`・`fixA_slabs.py` は名前「コンクリート」で選ぶ。別の言語・テンプレートでは、番号の材料が違う物になるか、名前が見つからずに止まる。その時は2つのスクリプトの先頭の番号・名前を、自分のテンプレートの材料に合わせて書き換える。
- Python を書いて実行できる AI エージェント（実験は Claude Opus 5.5）
- `run_sheets.sh` を動かす bash（Windows なら Git Bash など）

AI と Archicad の接続の入れ方は、セットアップ資料（https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja）と
スライド（https://docs.google.com/presentation/d/11fd7nvZPuE5BPmIBTQYlUanp_OZPNibPhbAnpD_UStg/edit?usp=sharing）。
ChatGPT Codex（デスクトップ版）に配布のプロンプトを貼ると、AI が Rhino / Grasshopper または Archicad との接続を入れて設定し、接続の確認としてバルセロナ・パビリオンを組む流れ。

## 手順（コマンド）

各段のコマンドと、人に頼む GUI の操作は、段ごとの指示ファイル（`prompts/00_prepare.md`・`05_sections.md`・`06_fix_model.md`・`10_all_sheets.md`・`18_rename_and_export.md`・`30_inspect_and_fix.md`、と実験の指示の末尾の「キットで足したこと」）に書いた。人が手で追う時も同じ順でよい。
概要：`check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` → 指示 `01_`・`02_`（→ `check_grid.py`）→ `make_sections.py create`（＋GUI：断面の窓6つを開く）→ `make_sections.py shoot` → モデルの直し `fixA_*`・`layer_found.py` → 指示 `10_`〜`17_`（`run_sheets.sh` または1本ずつ。1本ごとに `check_connection.py --save`）→ GUI：参照ID を A・B に → `export_png.py`・`check_levels.py` → 直しの指示を書いて流す。

### 自分のエージェントで指示を流す

指示ファイル（`prompts/*.md`）は、特定のエージェントに依存しない普通の文章。エージェントを**キットのフォルダで**起動し、新しい会話に次の1行だけを入力する（段 0 は `prompts/00_prepare.md`、段 1 以降は `work/prompts/…`）。

> 「`work/prompts/01_model_M.md` を読んで、指示どおりに作業してください」

- 実験も同じ形（新しい会話に「〜.md を読んで、〜作業してください」の1行）で流した。実験のエージェントは Hermes Agent。
- `work/prompts/` は `prepare_workdir.py` が作る。`<KIT>`（作業フォルダ）・`<KITROOT>`（キット）・「port は 19723」を実際の値に置き換えた版。`prepare_workdir.py` を使わない場合は、これらを手で置き換える。
- 1つの指示が終わってから次を入れる。指示ごとに新しい会話にすると、前の図の値を使い回さない（実験は1指示 = 1つの新しい会話）。
- 例（実験で使った物ではなく、同じことをする方法の例）：
  - Claude Code：キットのフォルダで `claude` を起動して上の1行を入力。まとめて流す時は `AGENT_CMD='claude -p --dangerously-skip-permissions'`
  - Codex：キットのフォルダで `codex` を起動して上の1行を入力。まとめて流す時は `AGENT_CMD='codex exec --full-auto'`
  - Hermes Agent など、ほかのエージェント：対話で上の1行を入力。まとめて流す時は、そのエージェントの「1回だけ実行して終わる」コマンドを `AGENT_CMD` に入れる
  - 権限の確認を飛ばす設定は、作業フォルダと Archicad だけを触る前提で使う。コマンドの書き方は各エージェントの説明書で確かめる。
- 指示の中の「session_search、honcho、delegate は使わない」は、実験で使ったエージェントの機能名。ほかのエージェントでは「記憶や過去の会話を使わない」と読み替える（無視しても動く）。
- 操作のコツと点検の手順は `skills/` にある（[skills/README.md](skills/README.md)。エージェントへの渡し方も）。

### かかった時間（実験の記録から。目安）

| 手順 | 時間 | 出どころ |
| --- | --- | --- |
| 家を組む（`01_`） | 約14分 | 録画 |
| 間取りと通り芯（`02_`） | 約18分 | 連続実行の記録（開始・終了の時刻） |
| 8枚を描く（`10_`〜`17_`） | 約2時間50分（断面 30〜35分/枚、立面 14〜19分/枚、平面 12〜26分/枚） | 同上 |
| 直し1周 | 1枚 5〜30分。1周で約1〜1.5時間 | 同上。平面は30分の上限で止まったことがある |
| モデルの直し | スクリプトは数秒〜数十秒ずつ | — |

AI の考える時間が大半。ルールの項目を増やすと伸びる。

## 入っているもの

- `README.md`（建築家向け）・`AI_GUIDE.md`（AI 向けの索引）・`TECHNICAL.md`（このファイル）。英語版は `README.en.md`・`AI_GUIDE.en.md`・`TECHNICAL.en.md`
- `inputs/`
  - `rhino_house.py`：元にした家（Rhino のスクリプト、単位 mm）。前の実験「[外観の絵だけ vs 絵＋図面](../2026-11_image-vs-drawing-3d/)」と同じ家で、窓と仕上げを足した版
  - `rhino_house.jpg`：その見た目
  - `layout_1F.jpg`・`layout_2F.jpg`：間取りの図（架空。間仕切り・部屋・階段を入れる指示で使った）
- `prompts/`
  - 実験の指示（`01_`・`02_`・`03_`・`04_`・`10_`〜`17_`・`20_`〜`25_`）：原文。パスだけ `<KIT>/` に置き換え、末尾に「キットで足したこと」（始める前の確認・保存・記録・次の1行）を追記（下の「流れ」の表）
  - 公開用に書いた段の指示：`00_prepare`（準備）・`05_sections`（立面・断面の線）・`06_fix_model`（モデルの直し）・`10_all_sheets`（8枚を順に）・`18_rename_and_export`（参照ID と書き出し）・`30_inspect_and_fix`（点検と直し1周）。実験で実験者の AI が直接行った作業を、1行で流せる形に書いた物。この形では Archicad で流していない
- `rules/`：作図ルール（立面・平面・断面）。AI はこれと Archicad から読める情報だけで描いた
- `skills/`：AI エージェントに渡す知識（作図ルールの案内、[Archicad 操作のコツ](skills/archicad-operation.md)、[点検と直しの指示の作り方](skills/inspection.md)）
- `scripts/`
  - `tapir_http.py`：Archicad の JSON API ＋ Tapir の命令を送る最小のクライアント
  - 準備と実行：`check_connection.py`（接続の確認・ポートを探す `--scan`・白紙か数える `--count`・保存 `--save`）、`prepare_workdir.py`（作業フォルダ）、`setup_stories.py`（階）、`check_grid.py`（通り芯ファイルの確認と形の統一）、`make_sections.py`（立面・断面の線）、`run_sheets.sh`（1枚ずつ流して保存）
  - モデルの直し：`fixA_snapshot.py` → `fixA_comps.py` → `fixA_walls.py` → `fixA_slabs.py` → `fixA_found.py` → `fixA_raise.py` → `layer_found.py`（＋必要なら `fixA_del2d.py`）
  - 点検：`export_png.py`（8枚を高解像度の PNG と文字に）、`check_levels.py`（レベル表記の照合）
  - `grid.json`：実験で AI が間取りの回で決めた通り芯（記録。`prepare_workdir.py --with-grid` で作業フォルダに入れられる）
  - `record/walls_before_fixA.json`：実験のモデルの、直す前の壁の控え（記録。要素 ID はそのモデルだけの物で、ほかのモデルには使えない）
- `results/`：仕上がりの8枚（`1_P1`〜`8_EW`）、断面の直す前・後（`sa_before_after.jpg`）、スキルなし／ありの南立面（`noskill_vs_skill.jpg`。11月14日、少し前の版の家）
- `images/`：README の画像（`step_house_data.jpg`＝入力を並べた物、`step_sheet_detail.jpg`＝`results/3_SA.jpg` の一部を切り抜いた物）

### スクリプトの出どころ

| スクリプト | 出どころ |
| --- | --- |
| `fixA_comps.py`・`fixA_walls.py`・`fixA_found.py`・`tapir_http.py` | 実験で使った物（パスとポートだけ一般化） |
| `layer_found.py` | 実験で使った物に、あとから短いコマンドで行った「床・敷地・水盤も同じ画層へ」を足して1本に |
| `make_sections.py`・`export_png.py`・`setup_stories.py`・`fixA_del2d.py` | 実験の前後で使ったスクリプトを一般化（窓を ID でなく名前で探す、パス・撮影範囲を引数に。`fixA_del2d.py` の平面の部分は再構成） |
| `fixA_snapshot.py`・`fixA_raise.py` | 実験では短いコマンドで流した物を、記録から取り出してファイルにした（戻すスラブの選び方だけ ID から規則に） |
| `fixA_slabs.py` | 再構成。元は直すスラブを要素 ID で指定していた。同じ振り分けを高さと範囲の規則で行う（記録の値で同じ振り分けになることを確かめた） |
| `run_sheets.sh` | 実験の連続実行スクリプトを、どのエージェントでも使える形に |
| `check_connection.py`・`prepare_workdir.py`・`check_levels.py`・`check_grid.py` | 公開用に新しく書いた |

公開用に書き直したスクリプトは、文法の確認と、Archicad を使わない部分（作業フォルダ作り・計画の表示・文字の照合・通り芯ファイルの統一）の試し実行だけをしている。Archicad では流していない。

## 使ったもの

- Archicad
- Tapir（Archicad のアドオン。JSON API に命令を足すもの。ポート 19723）
- AI：Claude Opus 5.5（AI エージェント Hermes Agent で実行）
- 日付：2026年11月15〜16日
- 画像の後処理：Python 3 ＋ Pillow

## 流れ（実際にやった順）

| # | やったこと | 指示 | 録画・時間 |
| --- | --- | --- | --- |
| 1 | 白紙の Archicad に、Rhino の家（スクリプトと画像）を読んで外壁・床・屋根・窓・扉を1つずつ組む | `01_model_M.md` | 録画あり。約14分 |
| 2 | 間仕切り・内部の扉・階段・部屋を入れ、通り芯を1組決める（`grid.json`） | `02_interior_I.md` | 録画なし |
| 3 | 南立面を、作図ルールで線と塗りまで仕上げる | `03_south_elevation_recorded.md` ＋ `rules/作図ルール_立面.md`（この時点の版） | 録画あり。約10分 |
| 4 | 残りの図面を描く。途中で、屋根を突き抜けた間仕切りを直し 2D を消して描き直した | `04_fix_partition_F.md` | 録画なし |
| 5 | 断面が弱かったので、Hermes がモデルを直す（下の「モデルの直し」） | `scripts/` | 録画なし |
| 6 | 断面の作図ルールを新しく書き、8枚を1枚ずつ描き直す（1枚ごとに SaveProject） | `10_sheet_P1.md`〜`17_sheet_EW.md` | 録画なし |
| 7 | 実務の図面の描き方（作法）と比べ、Hermes が直しの指示を書いて AI に入れる | `20_`〜`25_`（例） | 録画なし |

キットの段（README の表）は、この流れから 3・4（モデルを直す前の描画）を除いた形。3・4 も試す時は、`05_sections` の後に `03_` を流し、`06_fix_model`（古い 2D を `fixA_del2d.py --apply` で消してから直す）に進む。断面・立面の線（`make_sections.py`）は、実験ではこの家の前のモデルで作った物を、白紙のプロジェクトにそのまま残して使った。

### 直しの回数

- 断面・立面：3回（2回目・3回目・4回目＝最後。西立面だけ2回）。例として A-A 断面の3回分を入れた（`20_`〜`22_`）。
- 平面：2回（2回目・最後）。1階は2回目が時間切れで途中で止まったので、やり直しを1回（`24_`）。例として1階平面の分を入れた（`23_`〜`25_`）。
- 直しの指示は、Hermes が図を画像と数値で点検して書き、そのまま AI に入れた（手順は [skills/inspection.md](skills/inspection.md)）。
- Hermes が Archicad の画面で直接したこと：断面の印の名前を A / B に変えた、立面・平面の書き出しで地中（基礎）の画層を隠した、AI が足した小さい部屋の面積表示（かえって分かりにくくなった物）を外した。

### モデルの直し（流れの5）

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

高さ：1FL＝GL+100、1CL＝GL+2850、2FL＝GL+3250、2CL＝GL+6600、軒高＝GL+6900、最高高さ＝GL+7600。

## 再現できないもの（詳しく）

- **AI の出力は毎回違う**：同じ指示・同じモデルでも、描かれる線・文字の位置・間取りの細部は回ごとに変わる。`results/` と同じ図にはならない。直しの指示（`20_`〜`25_`）は実験の図に対して書いた物なので、自分の図には合わない所がある（形の例として使う）。
- **見本にした実務の図面は公開していない**：作図ルールと点検の比較に使った、人が描いた図面は出せない。点検では、自分の事務所の図面か、`rules/` の作図ルールを見本にする（[skills/inspection.md](skills/inspection.md)）。
- **GUI でしかできない手順がある**：新しい断面の窓を一度開く（版によって）、断面記号の参照ID の変更、落ちた後の復元の選択。
- **Archicad の版・テンプレートの差**：材料名（「コンクリート」など）、画層・ペン、断面の窓の名前の付き方は、版や言語・テンプレートで変わることがある。スクリプトは日本語の既定テンプレートの名前で書いてある。
- **直しの指示を書く判断**：点検の手順は書いたが、何を重大と見るかは見本と見る人（AI）で変わる。

## 正直に書いておくこと（詳しく）

- 録画して時間を測ったのは、流れの1（約14分）と、流れの3の南立面（約10分）だけ。ほかの回は録画していない。「かかった時間」の表のほかの値は、連続実行の記録（各回の開始・終了の時刻）から読んだ目安。
- 録画した南立面は、モデルを直す前（流れの5より前）の版。`results/5_ES.jpg` は直した後に描き直した版で、録画の図とは違う。
- 直しの指示は全部 Hermes（AI）が書いた。8枚が今の形になるまで、断面・立面は3回、平面は2回直している。
- 残っている弱いところ：車庫の壁が二重に見える（モデルに 0.3m 離れた壁が2枚ある）／1階平面に、スラブの角の円弧が見えている所がある／A-A 断面で、梁の所に小さい白いすき間がある／X6 の基礎にすき間がある。
- 寸法は 2D の線と文字で、モデルを変えても追従しない（次の回で扱う）。
- 図面8枚を続けて描かせている間に、Archicad が2回落ちた。対策として、1枚ごとに保存し、指示で `GetElementsInDrawOrder` を使わないようにした。
- 作図ルールは、実務の図面の描き方（作法）を整理したもの。形・間取り・数値は写していない。公開版では、元にした図面の件数と内部のファイル名を外した（描き方の中身は同じ）。南立面の録画の回は、`rules/作図ルール_立面.md` の最後の「11/16 の点検で足した決まり」が入る前の版を使った。
- 家は架空。1回ずつの試行で、AI や回数を変えると結果は変わる。
- キットの段の指示（00・05・06・10_all_sheets・18・30）と、実験の指示の末尾に足した「キットで足したこと」は公開用に書いた物で、Archicad で通しでは流していない。

## パスについて

- 指示文の `<KIT>/` は作業フォルダ（指示が読むファイルを置いた場所）、`<KITROOT>/` はキットのフォルダ（`scripts/` がある所）に読み替える。`python scripts/prepare_workdir.py` を使うと、キットの中に `work/` を作って置き換えまで済む（何度流してもよい。`grid.json`・`progress.md`・保存した `.pln` は消さない）。
- 手で読み替える時は、`scripts/tapir_http.py`・`rules/*.md`・`inputs/` の中身を1つのフォルダの直下に置き、指示の `<KIT>/` をそのフォルダに置き換える。指示の `rhino_house.png`・`layout_1F.png` は、この公開版では `.jpg` なので、変換するか読み替える。
- スクリプトは、同じフォルダの `tapir_http.py`・`fixA_comps.json`・`walls_before_fixA.json` などを読み書きする（実行するとできる。`.gitignore` 済み）。書き出しは `<KITROOT>/out/`（キットの中の out）。
- ポート：環境変数 `ARCHICAD_PORT` → `work/archicad_port.txt`（`check_connection.py --scan` が見つけた番号を書く）→ 19723 の順に使う（`tapir_http.default_port()`）。`prepare_workdir.py` は、指示文の「port は 19723」をこの番号に置き換える。
- 進み具合は `work/progress.md` に1行ずつ（各指示の末尾の「キットで足したこと」が書かせる）。再開はここを読む。
