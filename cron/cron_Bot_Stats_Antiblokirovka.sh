#!/bin/sh

SCRIPT_DIR="/home/c/ck60067/borodulin.expert/public_html/my_script/bot-telegram-lid-magnita"
VENV_PY="/home/c/ck60067/venv/bin/python"
LOG_FILE="/home/c/ck60067/cron_Bot_Stats_Antiblokirovka.log"

export PYTHONIOENCODING="utf-8"

cd "$SCRIPT_DIR" || exit 1

if [ ! -x "$VENV_PY" ]; then
    echo "$(date -Iseconds) python not found at $VENV_PY" >> "$LOG_FILE"
    exit 1
fi

echo "$(date -Iseconds) build_stats start" >> "$LOG_FILE"
"$VENV_PY" build_stats.py >> "$LOG_FILE" 2>&1
