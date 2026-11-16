#!/usr/bin/env bash
# 図面を1枚ずつ AI エージェントに描かせ、1枚ごとに Archicad を保存する（保存に失敗したら止める）。
#
# 使い方（キットのフォルダで。先に python scripts/prepare_workdir.py で work/ を作っておく）：
#   AGENT_CMD='claude -p --dangerously-skip-permissions' bash scripts/run_sheets.sh
#   AGENT_CMD='codex exec --full-auto' bash scripts/run_sheets.sh
#   SHEETS='12_sheet_SA 13_sheet_SB' AGENT_CMD='...' bash scripts/run_sheets.sh      # 一部だけ
#   SHEETS='20_fix_SA_round2' AGENT_CMD='...' bash scripts/run_sheets.sh             # 直しの指示も同じ形で流せる
#
# 変数：
#   AGENT_CMD  必須。最後の引数に指示文を1つ受け取って、終わったら戻る非対話のコマンド。
#              上の例は書いた時点のもの。各エージェントの「非対話で1回だけ実行」の書き方は、その説明書で確かめる。
#              権限確認を飛ばす設定は、この作業用フォルダと Archicad だけを触る前提で使う。
#   WORK       作業フォルダ（既定 <KIT>/work）。エージェントはここで起動する。
#   SHEETS     流す指示（prompts/ のファイル名から .md を除いた物）。既定は 10〜17 の8枚。
#   MAX_SEC    1枚の上限秒（既定 2700＝45分。注記の多い平面は 30 分では足りなかった）。timeout が無ければ上限なし。
#   PY         Python（既定 python）。ARCHICAD_PORT でポートを変えられる（既定 19723）。
#
# 実験でのやり方（同じ形）：1枚ごとに別のプロセスでエージェントを起動し、終わるたびに外から SaveProject を送った。
# 8枚を続けて描かせた時、エージェントは自分では保存せず、途中で Archicad が落ちて、保存前の状態に戻りかけた。
# Archicad に命令するエージェントは同時に1つだけにする（このスクリプトは順番に1つずつ流す）。
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
KIT="$(dirname "$HERE")"
: "${AGENT_CMD:?AGENT_CMD を指定する（例：AGENT_CMD='codex exec --full-auto'）}"
WORK="${WORK:-$KIT/work}"
SHEETS="${SHEETS:-10_sheet_P1 11_sheet_P2 12_sheet_SA 13_sheet_SB 14_sheet_ES 15_sheet_EN 16_sheet_EE 17_sheet_EW}"
MAX_SEC="${MAX_SEC:-2700}"
PY="${PY:-python}"
LOG="$WORK/logs"
mkdir -p "$LOG"
[ -d "$WORK/prompts" ] || { echo "$WORK/prompts が無い。先に $PY scripts/prepare_workdir.py"; exit 2; }
"$PY" "$HERE/check_connection.py" || { echo "Archicad に届かない。止める"; exit 2; }
TO=""; command -v timeout >/dev/null 2>&1 && TO="timeout $MAX_SEC"

for s in $SHEETS; do
  f="$WORK/prompts/$s.md"
  [ -f "$f" ] || { echo "== $s：$f が無い。飛ばす"; continue; }
  echo "== $s $(date +%T)"
  msg="$f を読んで、そのとおりに作業してください。"
  ( cd "$WORK" && $TO $AGENT_CMD "$msg" ) > "$LOG/$s.txt" 2>&1
  echo "rc=$? $(date +%T)（記録：$LOG/$s.txt）"
  "$PY" "$HERE/check_connection.py" --save || { echo "SAVE FAILED（Archicad が落ちた？）。止める。再開は、最後に保存した .pln を開いて、残りの SHEETS だけ流す"; exit 3; }
done
echo "== 終わり $(date +%T)。次：python scripts/export_png.py で書き出して点検（skills/inspection.md）"
