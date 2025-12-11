# utils.py
# Вспомогательные функции (в т.ч. для анализа статистики)

import os
import json
import shutil
from collections import defaultdict
from datetime import datetime

from config import DATA_DIR, LOGS_DIR
from storage import EVENTS_FILE, USERS_FILE


def _ts():
    return datetime.now().isoformat()


def _backup_file(path: str, suffix: str = None):
    """
    Делает резервную копию файла рядом с исходником.
    Название: <name>.bak-<timestamp> или с доп. суффиксом.
    """
    if not os.path.isfile(path):
        return
    base, ext = os.path.splitext(path)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if suffix:
        backup_path = f"{base}.{suffix}.bak-{ts}{ext}"
    else:
        backup_path = f"{base}.bak-{ts}{ext}"
    try:
        shutil.copy2(path, backup_path)
    except Exception:
        pass


def safe_load_json(path: str, default):
    """
    Безопасно читает JSON. При ошибке делает бэкап битого файла и возвращает default.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        _backup_file(path, "corrupt")
        return default


def read_events(skip_rows: int = 0):
    """
    Читает events.csv и возвращает (events, total_rows), где total_rows — число
    строк с данными (без заголовка). Можно пропускать первые skip_rows, чтобы
    обрабатывать только новые события.
    """
    events = []
    total_rows = 0
    if not os.path.isfile(EVENTS_FILE):
        return events, total_rows

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            header = True
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if header:
                    header = False
                    continue

                total_rows += 1
                if total_rows <= skip_rows:
                    continue

                parts = line.split(";")
                if len(parts) < 9:
                    # Пропускаем битую строку
                    continue

                ts, chat_id, user_id, ev, platform, theme, lead_type, creative, extra = parts
                events.append(
                    {
                        "timestamp": ts,
                        "chat_id": chat_id,
                        "user_id": user_id,
                        "event": ev,
                        "platform": platform,
                        "theme": theme,
                        "lead_type": lead_type,
                        "creative": creative,
                        "extra": extra,
                    }
                )
    except Exception:
        # Бэкап битого файла и возврат пустого списка
        _backup_file(EVENTS_FILE, "corrupt")
        try:
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "timestamp;chat_id;user_id;event;"
                    "platform;theme;lead_type;creative;extra\n"
                )
        except Exception:
            pass
        return [], 0

    return events, total_rows


def read_users():
    """
    Читает users.json безопасно, при ошибке делает бэкап и возвращает {}.
    """
    if not os.path.isfile(USERS_FILE):
        return {}
    data = safe_load_json(USERS_FILE, {})
    if isinstance(data, dict):
        return data
    return {}
