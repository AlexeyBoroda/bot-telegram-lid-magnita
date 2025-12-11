#!/bin/sh

SCRIPT_DIR="/home/c/ck60067/borodulin.expert/public_html/my_script/bot-telegram-lid-magnita"
VENV_PY="/home/c/ck60067/venv/bin/python"
LOG_FILE="/home/c/ck60067/cron_Bot_Antiblokirovka.log"
PID_FILE="$SCRIPT_DIR/tmp/bot_polling.pid"

export PYTHONIOENCODING="utf-8"

cd "$SCRIPT_DIR" || exit 1

mkdir -p tmp

# Если бот уже запущен — выходим (по pid-файлу)
if [ -f "$PID_FILE" ]; then
    old_pid="$(cat "$PID_FILE" 2>/dev/null)"
    if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
        exit 0
    fi
fi

# Проверяем наличие интерпретатора
if [ ! -x "$VENV_PY" ]; then
    echo "$(date -Iseconds) python not found at $VENV_PY" >> "$LOG_FILE"
    exit 1
fi

echo $$ > "$PID_FILE"
"$VENV_PY" bot_polling.py >> "$LOG_FILE" 2>&1
rm -f "$PID_FILE"
