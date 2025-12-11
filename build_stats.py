# build_stats.py
# Построение агрегированной статистики по events.csv и users.json

import os
import json
from collections import defaultdict
from datetime import datetime

from config import STATS_DIR
from utils import read_events, read_users


STATS_FILE = os.path.join(STATS_DIR, "stats.json")


def build_stats():
    events = read_events()
    users = read_users()

    # --- Базовые счётчики ---

    total_events = len(events)

    # Уникальные пользователи
    all_users = set()
    users_with_lead = set()

    # Для динамики по дням
    events_by_day = defaultdict(int)
    leads_by_day = defaultdict(int)

    # Структура по платформам / темам / типам / креативам
    by_platform_events = defaultdict(int)
    by_platform_users = defaultdict(set)

    by_theme_events = defaultdict(int)
    by_theme_users = defaultdict(set)

    by_lead_type_events = defaultdict(int)
    by_lead_type_users = defaultdict(set)

    by_creative_events = defaultdict(int)
    by_creative_users = defaultdict(set)

    # Какие креативы приводят больше уникальных людей
    creative_users_full_key = defaultdict(set)  # ключ: THx_TT_NN

    # Какая тема даёт больше лидов на пользователя
    leads_by_theme_users = defaultdict(set)

    for ev in events:
        user_id = ev["user_id"]
        event = ev["event"]
        platform = ev["platform"] or ""
        theme = ev["theme"] or ""
        lead_type = ev["lead_type"] or ""
        creative = ev["creative"] or ""
        ts = ev["timestamp"]

        all_users.add(user_id)

        # Парс даты (день)
        day = None
        try:
            # isoformat
            dt = datetime.fromisoformat(ts)
            day = dt.date().isoformat()
        except Exception:
            pass

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

    # Преобразуем множества в числа
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
        "users_raw": users,  # для доп. анализа на дашборде при желании
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
