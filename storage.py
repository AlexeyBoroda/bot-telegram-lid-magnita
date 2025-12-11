# storage.py
# Работа с users.json и events.csv

import os
import json
from datetime import datetime

from config import DATA_DIR, LOGS_DIR


USERS_FILE = os.path.join(DATA_DIR, "users.json")
EVENTS_FILE = os.path.join(LOGS_DIR, "events.csv")


def _ensure_files():
    """Создаём файлы при необходимости."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except Exception:
            pass

    if not os.path.exists(LOGS_DIR):
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
        except Exception:
            pass

    if not os.path.isfile(USERS_FILE):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    if not os.path.isfile(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "timestamp;chat_id;user_id;event;"
                    "platform;theme;lead_type;creative;extra\n"
                )
        except Exception:
            pass


def load_users():
    """Загружает словарь пользователей из users.json."""
    _ensure_files()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users: dict):
    """Сохраняет словарь пользователей в users.json."""
    _ensure_files()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def update_user(
    user_id: int,
    chat_id: int = None,
    platform: str = None,
    theme: str = None,
    lead_type: str = None,
    creative: str = None,
    lead_sent: bool = None,
):
    """
    Обновляет / создаёт запись о пользователе.

    Поля:
        - chat_id
        - platform (yt, vk, tg, ...)
        - theme (TH1, TH2, TH3, TH4)
        - lead_type (CL, MG, QZ)
        - creative (01, 02, ...)
        - lead_sent (bool) — выдавался ли лид-магнит хоть раз
    """
    users = load_users()
    key = str(user_id)
    data = users.get(key, {})

    if chat_id is not None:
        data["chat_id"] = chat_id
    if platform is not None:
        data["platform"] = platform
    if theme is not None:
        data["theme"] = theme
    if lead_type is not None:
        data["lead_type"] = lead_type
    if creative is not None:
        data["creative"] = creative
    if lead_sent is not None:
        data["lead_sent"] = bool(lead_sent)

    users[key] = data
    save_users(users)


def log_event(
    user_id: int,
    event: str,
    platform: str = "",
    theme: str = "",
    lead_type: str = "",
    creative: str = "",
    extra: str = "",
):
    """
    Пишет строку в events.csv в формате:
    timestamp;chat_id;user_id;event;platform;theme;lead_type;creative;extra
    """
    _ensure_files()
    users = load_users()
    udata = users.get(str(user_id), {})
    chat_id = udata.get("chat_id", "")

    ts = datetime.now().isoformat()
    line = (
        f"{ts};{chat_id};{user_id};{event};"
        f"{platform};{theme};{lead_type};{creative};{extra}\n"
    )

    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
