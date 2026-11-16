🇯🇵 日本語 | [🇺🇸 English](AI_GUIDE.en.md)

# AI_GUIDE：この実験を再現する AI エージェントへの索引

あなた（AI エージェント）は、このフォルダ（以下 **キット**）を使って、建築家のユーザーと一緒に
「白紙の Archicad に家を組み、作図ルールに沿って図面8枚を描き、点検して直す」を再現します。

**手順の本体は `prompts/` の指示ファイルです。** ユーザーは各段で、新しい会話に次の形の1行を貼ります。
「`<指示ファイル>` を読んで、指示どおりに作業してください」
各指示ファイルは、それだけで動くように書いてあります（前の段が済んでいるかの確認、保存、記録、次に貼る1行の案内まで）。
指示ファイルの名前が無いまま「このフォルダの AI_GUIDE.md を読んで、白紙の Archicad に家を組んで」のように頼まれた時は、下の表で今どの段かを判断し（`work/progress.md` があれば読む）、その段の指示ファイルを読んで進めてください。

## 段と指示ファイル

| 段 | ユーザーが貼る1行の中のファイル | 中身 | 人の画面操作 |
| --- | --- | --- | --- |
| 0 | `prompts/00_prepare.md` | 接続の確認、`work/` 作り（`prepare_workdir.py`）、階の設定と保存 | 空のプロジェクトを開く（必要な時） |
| 1 | `work/prompts/01_model_M.md` | 外形を組む（実験の原文＋キットの追記） | なし |
| 2 | `work/prompts/02_interior_I.md` | 間取りと通り芯（`work/grid.json`） | なし |
| 3 | `work/prompts/05_sections.md` | 立面・断面の線（`make_sections.py`） | 断面図の窓6つを1回ずつ開く |
| 4 | `work/prompts/06_fix_model.md` | 層・基礎・1FL＝GL+100（`fixA_*`・`layer_found.py`） | なし |
| 5 | `work/prompts/10_all_sheets.md`（または `10_sheet_P1`〜`17_sheet_EW` を1本ずつ） | 8枚を描く。1枚ごとに保存 | 落ちた時に開き直す |
| 6 | `work/prompts/18_rename_and_export.md` | 断面記号の参照ID を A・B に、8枚を画像に（`export_png.py`） | 参照ID の変更 |
| 7 | `work/prompts/30_inspect_and_fix.md` | 点検、直しの指示（`work/prompts/30_fix_*.md`）、直し、作図ルールを育てる | なし（指摘を書き足す） |

- `work/prompts/` は段 0 の `prepare_workdir.py` が作ります。指示の中の `<KIT>`（作業フォルダ）・`<KITROOT>`（キット）・ポートは、ここで実際の値に置き換わります。キットの `prompts/` の元のファイルは書き換えません。
- `03_south_elevation_recorded`・`04_fix_partition_F`・`20_`〜`25_` は実験の記録（例）です。ふだんの順では使いません（各ファイルの末尾に使い方を書いてあります）。

## どの段でも守る決まり

1. **ユーザーは建築家で、プログラマーではない。** 返事はユーザーと同じ言語で、建築の言葉で短く。コマンド、パス、プログラム用語を見せない（要る時はひとことで言い換える）。
2. **コマンドは全部あなたが実行する。** ユーザーに実行を頼まない。
3. **画面の操作が要る時だけユーザーに頼む。** 1回に1つ、メニューの場所まで書き、「終わったら『できた』と送ってください」と添えて待つ。
4. **Archicad への命令は、いつも1本ずつ。** 2つのスクリプトやエージェントから同時に送らない。命令の間、ユーザーに Archicad の画面を触らないよう頼む。
5. **1つの指示（1枚の図）が終わるたびに保存する**（`python scripts/check_connection.py --save`）と、`work/progress.md` に1行の記録。
6. **結果を作らない。** 失敗は平易に伝え、次の手を提案する。
7. **触ってよいのは、キットの中と、このために開いた Archicad のプロジェクト（house_from_scratch）だけ。** `make_sections.py create` はプロジェクトの断面マーカーを全部消すので、ほかのプロジェクトでは流さない。
8. 指示の中の「session_search、honcho、delegate は使わない」は、実験で使ったエージェント（Hermes Agent）の機能名。「記憶・過去の会話・ほかの AI への丸投げを使わない」と読み替える。
9. つながらない・Tapir が無い時は、セットアップ資料（日本語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja ／英語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en）を案内して止まる。

## 再開するとき

「続きをやって」「次は何？」と言われたら、`work/progress.md` を読み、`python scripts/check_connection.py` でつながりを確かめてから、終わっていない段の1行をユーザーに案内する（または、その指示ファイルを読んで進める）。

## 参考

- 操作のコツ（落ちない送り方、命令の書き方）：[skills/archicad-operation.md](skills/archicad-operation.md)
- 点検と直しの指示の作り方：[skills/inspection.md](skills/inspection.md)
- スキル（rules・skills）のエージェントへの渡し方：[skills/README.md](skills/README.md)
- ファイルの一覧、スクリプトの出どころ、パスの扱い、手で流す方法：[TECHNICAL.md](TECHNICAL.md)
