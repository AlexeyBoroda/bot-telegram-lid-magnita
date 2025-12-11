# bot_polling.py
# Telegram-бот "Антиблокировка" (polling-режим + запуск через cron)

import time
import traceback

from telegram import (
    Bot,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)

from config import BOT_TOKEN, CHANNEL_ID, get_lead_file_path
from config import FREE_URL, BASE_URL, PRO_URL
from storage import update_user, log_event, load_users


# --- Вспомогательные функции ---

def parse_start_param(param: str):
    """
    Ожидаемый формат:
        <platform>_<theme>_<lead_type>_<creative>
    Примеры:
        yt_TH1_CL_01
        vk_TH2_MG_02

    Возвращает (platform, theme, lead_type, creative).
    Если строка кривая — вынимаем максимум возможного.
    """
    platform = ""
    theme = ""
    lead_type = ""
    creative = ""

    if not param:
        return platform, theme, lead_type, creative

    parts = param.split("_")
    if len(parts) >= 1:
        platform = parts[0]
    if len(parts) >= 2:
        theme = parts[1]
    if len(parts) >= 3:
        lead_type = parts[2]
    if len(parts) >= 4:
        creative = parts[3]

    return platform, theme, lead_type, creative


# --- Обработчики команд и кнопок ---

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Параметр после /start
    args = context.args or []
    raw_param = args[0] if args else ""

    platform, theme, lead_type, creative = parse_start_param(raw_param)

    # Сохраняем информацию о пользователе и источнике
    update_user(
        user.id,
        chat_id=chat_id,
        platform=platform,
        theme=theme,
        lead_type=lead_type,
        creative=creative,
    )

    log_event(
        user.id,
        "start",
        platform=platform,
        theme=theme,
        lead_type=lead_type,
        creative=creative,
    )

    # Приветственное сообщение
    text = (
        "Привет! Я Алексей Бородулин.\n\n"
        "Ты попал в бота по теме безопасности расчётов и блокировок счетов. "
        "Сейчас я выдам тебе полезный материал — лид-магнит, а дальше "
        "предложу пройти курс «Как вести бизнес, чтобы не заблокировали счета».\n\n"
        "Сначала нужно подписаться на мой открытый канал — там я разбираю "
        "новости 115-ФЗ, кейсы блокировок и даю практические советы.\n\n"
        "👉 Шаг 1. Подпишись на канал.\n"
        "👉 Шаг 2. Нажми кнопку «✅ Уже подписался — выдать файл»."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Подписаться на канал",
                url=f"https://t.me/{CHANNEL_ID.lstrip('@')}",
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Уже подписался — выдать файл",
                callback_data="check_sub",
            )
        ],
    ])

    if update.message:
        update.message.reply_text(text, reply_markup=keyboard)


def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    query.answer()

    # Проверяем подписку
    is_member = False
    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ("member", "administrator", "creator"):
            is_member = True
    except Exception:
        is_member = False

    if not is_member:
        # Не подписан — снова даём кнопки
        text = (
            "Похоже, ты ещё не подписан на канал.\n\n"
            "Подпишись, пожалуйста, чтобы получить доступ к материалам.\n\n"
            "После подписки нажми «✅ Уже подписался — выдать файл»."
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_ID.lstrip('@')}",
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Уже подписался — выдать файл",
                    callback_data="check_sub",
                )
            ],
        ])
        # Защита от ошибки "Message is not modified"
        if not query.message or query.message.text != text:
            query.edit_message_text(text, reply_markup=keyboard)
        return

    # Подписка есть — достаём данные по пользователю
    users = load_users()
    udata = users.get(str(user.id), {})

    platform = udata.get("platform", "")
    theme = udata.get("theme", "")
    lead_type = udata.get("lead_type", "")
    creative = udata.get("creative", "")

    # Пытаемся найти файл лид-магнита
    lead_path = get_lead_file_path(theme, lead_type, creative)

    if not lead_path:
        msg = (
            "Подписка подтверждена ✅\n\n"
            "Но для этой комбинации темы / формата / креатива "
            "лид-магнит пока не настроен.\n\n"
            "Файла нет. Обратитесь к Алексею Бородулину."
        )
        # Тут текст почти всегда отличается, но на всякий случай проверяем
        if not query.message or query.message.text != msg:
            query.edit_message_text(msg)
        log_event(
            user.id,
            "lead_file_not_found",
            platform=platform,
            theme=theme,
            lead_type=lead_type,
            creative=creative,
            extra="no_file",
        )
        return

    # Отправляем файл
    try:
        sending_text = "Подписка подтверждена ✅\nОтправляю файл…"
        if not query.message or query.message.text != sending_text:
            query.edit_message_text(sending_text)

        with open(lead_path, "rb") as f:
            context.bot.send_document(
                chat_id=user.id,
                document=f,
                filename=lead_path.split("/")[-1],
                caption="📎 Твой файл-лид-магнит. Сохрани себе и внедряй.",
            )

        log_event(
            user.id,
            "lead_sent",
            platform=platform,
            theme=theme,
            lead_type=lead_type,
            creative=creative,
            extra="lead_type={}".format(lead_type),
        )

        update_user(user.id, lead_sent=True)

        # Предлагаем курс
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "▶️ Пройти бесплатный модуль (FREE)",
                    url=FREE_URL or "https://stepik.org/a/252809",
                )
            ],
            [
                InlineKeyboardButton(
                    "💼 Формат BASE",
                    url=BASE_URL or "https://stepik.org/a/252040",
                ),
                InlineKeyboardButton(
                    "⭐ Формат PRO",
                    url=PRO_URL or "https://stepik.org/a/252823",
                ),
            ],
        ])

        context.bot.send_message(
            chat_id=user.id,
            text=(
                "Если хочешь не только потушить пожар, но и выстроить систему "
                "так, чтобы банк изначально не считал твой бизнес рискованным — "
                "пройди курс «Как вести бизнес, чтобы не заблокировали счета».\n\n"
                "Выбирай формат и начинай уже сегодня 👇"
            ),
            reply_markup=kb,
        )

    except Exception:
        traceback.print_exc()
        query.edit_message_text(
            "Произошла ошибка при отправке файла.\n"
            "Попробуй позже или напиши Алексею Бородулину."
        )


def button_click_logger(update: Update, context: CallbackContext):
    """
    На будущее: если будешь использовать callback_data для кнопок курсов —
    здесь можно логировать клики.
    Сейчас все кнопки с URL, поэтому Telegram не присылает сюда события.
    """
    query = update.callback_query
    user = query.from_user
    data = query.data or ""
    query.answer()

    log_event(user.id, "button_click", extra=data)


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN пустой. Заполни .env и перезапусти.")
        return

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_sub$"))
    dp.add_handler(CallbackQueryHandler(button_click_logger, pattern="^click_"))

    # Короткий цикл polling, чтобы дружить с cron (служит ~50 секунд)
    updater.start_polling()
    time.sleep(50)
    updater.stop()
    updater.is_idle = False


if __name__ == "__main__":
    main()
