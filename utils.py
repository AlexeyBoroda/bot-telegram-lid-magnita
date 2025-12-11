# utils.py
# Вспомогательные функции (в т.ч. для анализа статистики)

import os
import json
from collections import defaultdict

from config import DATA_DIR, LOGS_DIR
from storage import EVENTS_FILE, USERS_FILE


def safe_load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_events():
    """
    Читает events.csv и возвращает список словарей:
    {
        "timestamp": "...",
        "chat_id": "...",
        "user_id": "...",
        "event": "...",
        "platform": "...",
        "theme": "...",
        "lead_type": "...",
        "creative": "...",
        "extra": "..."
    }
    """
    events = []
    if not os.path.isfile(EVENTS_FILE):
        return events

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

                parts = line.split(";")
                if len(parts) < 9:
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
        return []

    return events


def read_users():
    """
    Читает users.json и возвращает словарь:
    {user_id: {...}}
    """
    if not os.path.isfile(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
