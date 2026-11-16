# -*- coding: utf-8 -*-
# Rhino の中で、正解・A・B（と録画回）を同じ条件で撮る。Rhino の ScriptEditor（Python）で開いて実行する。
# AI 経由なら：Rhino 接続（MCP）の「Python を実行する」ツールに
#   exec(open('C:/path/to/kit/scripts/run_all_in_rhino.py', encoding='utf-8').read())
# を送る。出力は work/compare/<名前>/（sil_*.png・eye_*.png・model.3dm）。
# 注意：撮影中は Rhino の窓の大きさを変えない（平行投影の縮尺が変わり、重なり率が崩れる）。
import io
KIT = 'C:/path/to/kit/'   # ← このフォルダ（experiments/2026-11_image-vs-drawing-3d/）の絶対パスに書き換える
g = {'KIT_OVERRIDE': KIT}
exec(io.open(KIT + 'scripts/run_compare.py', encoding='utf-8').read(), g)
run = g['run']
WALLS = ('concrete', 'black_mortar', 'rammed_earth')
log = []
# 正解（図面どおり）。原点は図面のグリッドなので位置合わせしない
log.append(run(KIT + 'outputs/reference_v14.py', 'C_reference_v14', False, WALLS))
# 1回目（スクリプトを書かせた回）
log.append(run(KIT + 'outputs/A/model.py', 'A_image_only', True, WALLS))     # 絵だけ：原点が無いので左端・最前にそろえる
log.append(run(KIT + 'outputs/B/model.py', 'B_image_plus_drawing', False, WALLS))
# 2回目（Rhino で部分ごとに組んだ録画回）。公開画像は外観に寄せた打放し concrete_v6 で撮った。
# tex/concrete_v6/ が無ければ（make_concrete_v6.py 未実行なら）上と同じ3種で撮る。影絵（採点）は壁の素材に関係しない。
import os
LIVE_WALLS = ('concrete_v6',) if os.path.isdir(KIT + 'tex/concrete_v6/') else WALLS
log.append(run(KIT + 'run2_recorded/outputs/A/model.py', 'live_A', True, LIVE_WALLS))
log.append(run(KIT + 'run2_recorded/outputs/B/model.py', 'live_B', False, LIVE_WALLS))
result = ' | '.join(log)
