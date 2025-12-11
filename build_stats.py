# build_stats.py
# Построение агрегированной статистики по events.csv и users.json

import os
import json
from collections import defaultdict
from datetime import datetime

from config import STATS_DIR
from utils import read_events, read_users, safe_load_json


STATS_FILE = os.path.join(STATS_DIR, "stats.json")
DEFAULT_META = {
    "processed_events": 0,
    "events_by_day": {},
    "leads_by_day": {},
    "by_platform_events": {},
    "by_theme_events": {},
    "by_lead_type_events": {},
    "by_creative_events": {},
    "by_platform_users": {},
    "by_theme_users": {},
    "by_lead_type_users": {},
    "by_creative_users": {},
    "creative_users_full_key": {},
    "leads_by_theme_users": {},
    "all_users": [],
    "users_with_lead": [],
}


def _as_set_dict(value):
    return {k: set(v) for k, v in (value or {}).items()}


def _load_prev_meta():
    data = safe_load_json(STATS_FILE, {})
    if not isinstance(data, dict):
        return DEFAULT_META.copy()
    meta = data.get("meta", {}) or {}
    merged = DEFAULT_META.copy()
    merged.update(meta)
    return merged


def build_stats():
    prev_meta = _load_prev_meta()
    processed_before = max(int(prev_meta.get("processed_events", 0) or 0), 0)

    events, total_rows = read_events(skip_rows=processed_before)
    users = read_users()

    # Если файл урезан/пересоздан — начинаем с нуля
    if processed_before > total_rows:
        processed_before = 0
        events, total_rows = read_events(skip_rows=0)

    # --- Базовые структуры, подхватываем прошлые значения ---
    events_by_day = defaultdict(int, prev_meta.get("events_by_day", {}))
    leads_by_day = defaultdict(int, prev_meta.get("leads_by_day", {}))

    by_platform_events = defaultdict(int, prev_meta.get("by_platform_events", {}))
    by_theme_events = defaultdict(int, prev_meta.get("by_theme_events", {}))
    by_lead_type_events = defaultdict(int, prev_meta.get("by_lead_type_events", {}))
    by_creative_events = defaultdict(int, prev_meta.get("by_creative_events", {}))

    by_platform_users = _as_set_dict(prev_meta.get("by_platform_users"))
    by_theme_users = _as_set_dict(prev_meta.get("by_theme_users"))
    by_lead_type_users = _as_set_dict(prev_meta.get("by_lead_type_users"))
    by_creative_users = _as_set_dict(prev_meta.get("by_creative_users"))

    creative_users_full_key = _as_set_dict(prev_meta.get("creative_users_full_key"))
    leads_by_theme_users = _as_set_dict(prev_meta.get("leads_by_theme_users"))

    all_users = set(prev_meta.get("all_users", []))
    users_with_lead = set(prev_meta.get("users_with_lead", []))

    total_events = processed_before

    # --- Обрабатываем только новые события ---
    for ev in events:
        total_events += 1
        user_id = ev["user_id"]
        event = ev["event"]
        platform = ev["platform"] or ""
        theme = ev["theme"] or ""
        lead_type = ev["lead_type"] or ""
        creative = ev["creative"] or ""
        ts = ev["timestamp"]

        all_users.add(user_id)

        # Парс даты (день)
        try:
            day = datetime.fromisoformat(ts).date().isoformat()
        except Exception:
            day = None

        if day:
            events_by_day[day] += 1
            if event == "lead_sent":
                leads_by_day[day] += 1

        # Структура по платформам
        if platform:
            by_platform_events[platform] += 1
            by_platform_users[platform].add(user_id)

        # Структура по темам
        if theme:
            by_theme_events[theme] += 1
            by_theme_users[theme].add(user_id)

        # Структура по типам лид-магнитов
        if lead_type:
            by_lead_type_events[lead_type] += 1
            by_lead_type_users[lead_type].add(user_id)

        # Структура по креативам
        if creative:
            by_creative_events[creative] += 1
            by_creative_users[creative].add(user_id)

        # Лиды
        if event == "lead_sent":
            users_with_lead.add(user_id)
            if theme:
                leads_by_theme_users[theme].add(user_id)
            if theme and lead_type and creative:
                key_full = f"{theme}_{lead_type}_{creative}"
                creative_users_full_key[key_full].add(user_id)

    def convert_counts(events_dict, users_dict):
        out = []
        for k in sorted(events_dict.keys()):
            out.append(
                {
                    "key": k,
                    "events": events_dict[k],
                    "unique_users": len(users_dict.get(k, set())),
                }
            )
        return out

    stats = {
        "summary": {
            "total_events": total_events,
            "total_users": len(all_users),
            "users_with_lead": len(users_with_lead),
        },
        "events_by_day": dict(events_by_day),
        "leads_by_day": dict(leads_by_day),
        "by_platform": convert_counts(by_platform_events, by_platform_users),
        "by_theme": convert_counts(by_theme_events, by_theme_users),
        "by_lead_type": convert_counts(by_lead_type_events, by_lead_type_users),
        "by_creative": convert_counts(by_creative_events, by_creative_users),
        "best_creatives": [
            {
                "key": k,
                "unique_users": len(v),
            }
            for k, v in sorted(
                creative_users_full_key.items(),
                key=lambda item: len(item[1]),
                reverse=True,
            )
        ],
        "leads_by_theme_users": {
            theme: len(u_set) for theme, u_set in leads_by_theme_users.items()
        },
        "users_raw": users,
        "meta": {
            "processed_events": total_rows,
            "events_by_day": dict(events_by_day),
            "leads_by_day": dict(leads_by_day),
            "by_platform_events": dict(by_platform_events),
            "by_theme_events": dict(by_theme_events),
            "by_lead_type_events": dict(by_lead_type_events),
            "by_creative_events": dict(by_creative_events),
            "by_platform_users": {k: list(v) for k, v in by_platform_users.items()},
            "by_theme_users": {k: list(v) for k, v in by_theme_users.items()},
            "by_lead_type_users": {k: list(v) for k, v in by_lead_type_users.items()},
            "by_creative_users": {k: list(v) for k, v in by_creative_users.items()},
            "creative_users_full_key": {
                k: list(v) for k, v in creative_users_full_key.items()
            },
            "leads_by_theme_users": {
                k: list(v) for k, v in leads_by_theme_users.items()
            },
            "all_users": list(all_users),
            "users_with_lead": list(users_with_lead),
        },
    }

    if not os.path.exists(STATS_DIR):
        try:
            os.makedirs(STATS_DIR, exist_ok=True)
        except Exception:
            pass

    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    build_stats()
