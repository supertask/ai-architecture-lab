🇯🇵 日本語 | [🇺🇸 English](AI_GUIDE.en.md)

# AI_GUIDE：この実験を再現する AI エージェントへの索引

あなた（AI エージェント）は、このフォルダ（以下 **キット**）を使って、建築家のユーザーと一緒に
「白紙の Archicad に家を組み、作図ルールに沿って図面8枚を描き、点検して直す」を再現します。

**手順の本体は `prompts/` の指示ファイルです。** ユーザーは各段で、新しい会話に次の形の1行を貼ります。
「`<指示ファイル>` を読んで、指示どおりに作業してください」
指示ファイルに書いてあることだけを行ってください。段の順番、保存、次に貼る1行は、ユーザーが [README.md](README.md) の表を見て進めます（指示ファイルには書いてありません）。
指示ファイルの名前が無いまま頼まれた時は、README の表を示して、どの段から始めるかをユーザーに確かめてください。

## 指示ファイルと「実験で」

| 段（README の表） | ファイル | 中身 | 実験で |
| --- | --- | --- | --- |
| 1 | `prompts/00_prepare.md` | `check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` を流すだけ | 追加（未使用） |
| 2 | `work/prompts/01_model_M.md` | 外形を組む | 同じ指示で実行 |
| 3 | `work/prompts/02_interior_I.md` | 間取りと通り芯（`work/grid.json`） | 同じ指示で実行 |
| 4 | `work/prompts/05_sections.md` | `make_sections.py create` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 6 | `work/prompts/06_fix_model.md` | `fixA_snapshot` → `fixA_comps` → `fixA_walls` → `fixA_slabs --apply` → `fixA_found` → `fixA_raise` → `fixA_del2d --apply` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 7 | `work/prompts/12_sheet_SA` → `13_sheet_SB` → `14_sheet_ES` → `15_sheet_EN` → `16_sheet_EE` → `17_sheet_EW` → `10_sheet_P1` → `11_sheet_P2` | 1枚ずつ描く | 同じ指示で実行 |
| 9 | `work/prompts/18_export.md` | `layer_found.py` → `export_png.py` を流すだけ | 同じスクリプトを実行（指示文は今回追加） |
| 10 | `work/prompts/30_inspect_and_fix.md` | 点検、直しの指示を書く、直す | 追加（未使用） |
| 記録 | `03_south_elevation_recorded`・`04_fix_partition_F` | 実験の回の記録 | 同じ指示で実行 |
| 記録 | `20_`〜`25_` | 実験の直しの記録（そのときの失敗に合わせた指示。あなたの結果には当てはまらないことが多い） | 同じ指示で実行 |

段 0・5・8 は人が Archicad の画面で行います（空のプロジェクトを開く、断面の窓6つを開く、断面記号の参照ID を A・B に変える）。

- `work/prompts/` は段 1 の `prepare_workdir.py` が作ります。指示の中の `<KIT>`（作業フォルダ）・`<KITROOT>`（キット）・ポートは、ここで実際の値に置き換わります。キットの `prompts/` の元のファイルは書き換えません。
- 指示の中の「session_search、honcho、delegate は使わない」は、実験で使ったエージェント（Hermes Agent）の機能名。「記憶・過去の会話・ほかの AI への丸投げを使わない」と読み替えてください。
- 結果を作らないでください。スクリプトが失敗したら、出力をそのまま見せて止まります。
- Archicad への命令は、いつも1本ずつ。2つのスクリプトやエージェントから同時に送らないでください。
- つながらない・Tapir が無い時は、セットアップ資料（日本語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja ／英語 https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en）を案内して止まります。

## 参考

- 操作のコツ（落ちない送り方、命令の書き方）：[skills/archicad-operation.md](skills/archicad-operation.md)
- 点検と直しの指示の作り方：[skills/inspection.md](skills/inspection.md)
- スキル（rules・skills）のエージェントへの渡し方：[skills/README.md](skills/README.md)
- ファイルの一覧、実験でやった順、スクリプトの出どころ、パスの扱い：[TECHNICAL.md](TECHNICAL.md)
