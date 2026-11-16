#!/usr/bin/env bash
# 指示を1本ずつ、新しい AI エージェントの実行（＝新しい会話）に渡し、1本終わるごとに Archicad を保存する。
#
# 実験の連続実行と同じ形：1本ごとに別のプロセスでエージェントを起動して
# 「<指示ファイル> を読んで、指示どおりに作業してください。」の1行だけを渡し、終わったら外から SaveProject を送った。
# 保存に失敗したら（Archicad が落ちた可能性）止める。Archicad に命令するエージェントは同時に1つだけ（順番に流す）。
#
# 使い方（キットのフォルダで。先に prompts/00_prepare.md の段を済ませ、work/ がある状態で）：
#   AGENT_CMD='claude -p --dangerously-skip-permissions' bash scripts/run_sheets.sh
#   AGENT_CMD='codex exec --full-auto' bash scripts/run_sheets.sh
#   SHEETS='12_sheet_SA 13_sheet_SB' AGENT_CMD='...' bash scripts/run_sheets.sh      # 一部だけ
#
# 変数：
#   AGENT_CMD  必須。最後の引数に指示文を1つ受け取って、終わったら戻る非対話のコマンド。
#              上の2つは例（実験で使ったのは Hermes Agent）。書き方は各エージェントの説明書で確かめる。
#              権限確認を飛ばす設定は、この作業用フォルダと Archicad だけを触る前提で使う。
#   WORK       作業フォルダ（既定 <KIT>/work）。エージェントはここで起動する。
#   SHEETS     流す指示（prompts/ のファイル名から .md を除いた物）。既定は図面8枚を、実験と同じ順
#              （A-A → B-B → 南 → 北 → 東 → 西立面 → 1階 → 2階平面）。
#   MAX_SEC    1本の上限秒（既定 2400＝40分。実験と同じ）。timeout コマンドが無ければ上限なし。
#   PY         Python（既定 python）。ポートは ARCHICAD_PORT → work/archicad_port.txt → 19723。
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
KIT="$(dirname "$HERE")"
: "${AGENT_CMD:?AGENT_CMD を指定する（例：AGENT_CMD='codex exec --full-auto'）}"
WORK="${WORK:-$KIT/work}"
SHEETS="${SHEETS:-12_sheet_SA 13_sheet_SB 14_sheet_ES 15_sheet_EN 16_sheet_EE 17_sheet_EW 10_sheet_P1 11_sheet_P2}"
MAX_SEC="${MAX_SEC:-2400}"
PY="${PY:-python}"
LOG="$WORK/logs"
[ -d "$WORK/prompts" ] || { echo "$WORK/prompts が無い。先に prompts/00_prepare.md の段を済ませる"; exit 2; }
mkdir -p "$LOG"
TO=""; command -v timeout >/dev/null 2>&1 && TO="timeout $MAX_SEC"
save() { ( cd "$HERE" && "$PY" -c "import tapir_http as t; print('save', t.call(t.default_port(), 'SaveProject', {}, timeout=300))" ); }

for s in $SHEETS; do
  [ -f "$WORK/prompts/$s.md" ] || { echo "== $s：$WORK/prompts/$s.md が無い。飛ばす"; continue; }
  echo "== $s $(date +%T)"
  ( cd "$WORK" && $TO $AGENT_CMD "prompts/$s.md を読んで、指示どおりに作業してください。" ) > "$LOG/$s.txt" 2>&1
  echo "rc=$? $(date +%T)（記録：$LOG/$s.txt）"
  save || { echo "SAVE FAILED（Archicad が落ちた？）。止める。再開は、最後に保存した .pln を開いて、残りだけ SHEETS で流す"; exit 3; }
done
echo "== 終わり $(date +%T)"
