# 06 モデルを直す：スクリプトを順に流す

次のスクリプトを、この順に1本ずつ流してください（前のスクリプトが終わってから次へ）。

1. `python <KITROOT>/scripts/fixA_snapshot.py`
2. `python <KITROOT>/scripts/fixA_comps.py`
3. `python <KITROOT>/scripts/fixA_walls.py`
4. `python <KITROOT>/scripts/fixA_slabs.py --apply`
5. `python <KITROOT>/scripts/fixA_found.py`
6. `python <KITROOT>/scripts/fixA_raise.py`
7. `python <KITROOT>/scripts/fixA_del2d.py --apply`

- 1本ごとに、出力をそのまま見せる。
- エラーが出たら（終了コードが 0 でない時も）、そこで止めて、出力をそのまま報告する。直そうとしたり、先へ進んだり、同じスクリプトを流し直したりしない（`fixA_raise.py` は2回流すと2回上がる）。
- これ以外の作業はしない。
