# 00 準備：スクリプトを順に流す

キットのフォルダ（このファイルがある prompts フォルダの1つ上）で、次のスクリプトをこの順に1本ずつ流してください。

1. `python scripts/check_connection.py --scan`
2. `python scripts/prepare_workdir.py`
3. `python scripts/setup_stories.py work/house_from_scratch.pln`

- 1本ごとに、出力をそのまま見せる。
- エラーが出たら（終了コードが 0 でない時も）、そこで止めて、出力をそのまま報告する。直そうとしたり、先へ進んだりしない。
- これ以外の作業はしない。
