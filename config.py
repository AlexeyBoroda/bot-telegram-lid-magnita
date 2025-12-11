# config.py
# Конфигурация Telegram-бота "Антиблокировка"

import os
from dotenv import load_dotenv

# Базовая папка проекта (где лежит этот файл)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Загружаем .env из корня проекта
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Параметры бота и каналов ---

# Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# ID или @username канала, где проверяем подписку (например, @Borodulin_expert)
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()

# Ссылки на курсы (форматы Free / Base / PRO)
FREE_URL = os.getenv("FREE_URL", "").strip()
BASE_URL = os.getenv("BASE_URL", "").strip()
PRO_URL = os.getenv("PRO_URL", "").strip()

# --- Пути для данных и логов ---

# Папка с данными (users.json и т.п.)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Папка с логами событий (events.csv)
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Папка со статистикой (stats.json)
STATS_DIR = os.path.join(BASE_DIR, "stats")

# Папка с файлами лид-магнитов
LEADS_DIR = os.path.join(BASE_DIR, "assets", "leads")

# Создаём папки при необходимости
for path in (DATA_DIR, LOGS_DIR, STATS_DIR, LEADS_DIR):
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            # На shared-хостинге могут быть ограничения — молча игнорируем
            pass

# --- Словарь соответствия "тема + тип + креатив" → файл лид-магнита ---

"""
LEAD_FILES — маппинг:
    "THx_TT_NN" -> "имя файла в папке LEADS_DIR"

Где:
    TH1, TH2, TH3, TH4 — темы:
        TH1 — «Счёт уже заблокирован — что делать по шагам?»
        TH2 — «Как не попасть под блокировку (триггеры 115-ФЗ и ЗСК)»
        TH3 — «Документы для банка: что подготовить заранее»
        TH4 — «Как правильно отвечать банку / МВК»

    TT — тип лид-магнита:
        CL — чек-лист (checklist)
        MG — мини-гайд (mini-guide)
        QZ — квиз / мини-аудит (quiz)

    NN — номер креатива: 01, 02, 03 ...

Имя файла может быть ЛЮБЫМ (pdf/docx и т.д.), главное — правильно связать ключ и файл.

ВАЖНО:
    - Никаких общих/резервных файлов.
    - Если ключ не задан в LEAD_FILES или файл отсутствует на диске —
      бот НЕ подставляет ничего и пишет:
      «Файла нет. Обратитесь к Алексею Бородулину.»
"""

LEAD_FILES = {
    # Примеры — замени на свои реальные файлы по мере добавления
    "TH1_CL_01": "checklist_24h.pdf",
    # "TH1_CL_02": "TH1_checklist_case-02.pdf",
    # "TH1_MG_01": "TH1_miniguide_structured.pdf",
    # "TH2_CL_01": "block_account_steps_TH2_01.pdf",
    # "TH2_MG_01": "TH2_miniguide_v1.pdf",
    # "TH3_QZ_01": "TH3_quiz_01.pdf",
}


def get_lead_file_path(theme: str, lead_type: str, creative: str) -> str:
    """
    Возвращает ПОЛНЫЙ путь к файлу лид-магнита для заданной
    темы / типа / креатива.

    Ключ формируется строго как:
        "{theme}_{lead_type}_{creative}"  (например, "TH1_CL_01")

    Если:
        - ключа нет в LEAD_FILES, или
        - файла нет на диске,
    то возвращает пустую строку.
    """
    theme = (theme or "").strip()
    lead_type = (lead_type or "").strip()
    creative = (creative or "").strip()

    if not theme or not lead_type or not creative:
        return ""

    key = f"{theme}_{lead_type}_{creative}"
    filename = LEAD_FILES.get(key)

    if not filename:
        return ""

    full_path = os.path.join(LEADS_DIR, filename)
    if not os.path.isfile(full_path):
        return ""

    return full_path
