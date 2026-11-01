
"""
Бот кондитера на трёх языках (O'zbekcha / Русский / English).

Запуск:
    pip install -r requirements.txt
    python bot.py

Для Render:
    BOT_TOKEN и ADMIN_ID задаются через Environment Variables.
"""

import asyncio
import html
import json
import logging
import os

from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ======================= НАСТРОЙКИ =======================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8830908625:AAFjNO-JOdtT4asxxo4233OGhn7CY0stpPA")
ADMIN_ID = int(os.getenv("ADMIN_ID", "644114217"))

SHOP_NAME = "Mavluda Kitchen"
CHANNEL_URL = "https://t.me/kanditeer"
INSTAGRAM_URL = "https://www.instagram.com/movluda_kitchen/"

USERS_FILE = "users.json"

PHONE = "+(998)97 780-06-80"
BOT_USERNAME = "@Mavluda_kitchen_bot"

ADDRESS = {
    "ru": "Юнусобод 18-15-70",
    "uz": "Yunusobod 18-15-70",
    "en": "Yunusobod 18-15-70",
}

LANG_TITLES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

CHOOSE_LANG = "Tilni tanlang / Выберите язык / Choose your language:"


def is_set(url: str) -> bool:
    return url.startswith("http") and "ВАШ" not in url


def link_lines(lang: str) -> str:
    label = {
        "ru": "Канал",
        "uz": "Kanal",
        "en": "Channel",
    }[lang]

    out = ""

    if is_set(CHANNEL_URL):
        out += f"📢 {label}: {CHANNEL_URL}\n"

    if is_set(INSTAGRAM_URL):
        out += f"📷 Instagram: {INSTAGRAM_URL}\n"

    return out


TEXTS = {
    "welcome": {
        "ru": f"Добро пожаловать в «{SHOP_NAME}»! 🧁\nВыберите десерты в нашем канале и оставьте заявку здесь.",
        "uz": f"«{SHOP_NAME}»ga xush kelibsiz! 🧁\nShirinliklarni kanalimizdan tanlang va ariza qoldiring.",
        "en": f"Welcome to {SHOP_NAME}! 🧁\nChoose desserts in our channel and place your request here.",
    },

    "btn_channel": {
        "ru": "📢 Канал и Instagram",
        "uz": "📢 Kanal va Instagram",
        "en": "📢 Channel & Instagram",
    },

    "btn_request": {
        "ru": "📝 Оставить заявку",
        "uz": "📝 Ariza qoldirish",
        "en": "📝 Place an order",
    },

    "btn_contacts": {
        "ru": "📞 Контакты",
        "uz": "📞 Aloqa",
        "en": "📞 Contacts",
    },

    "btn_lang": {
        "ru": "🌐 Til / Язык / Language",
        "uz": "🌐 Til / Язык / Language",
        "en": "🌐 Til / Язык / Language",
    },

    "btn_cancel": {
        "ru": "❌ Отмена",
        "uz": "❌ Bekor qilish",
        "en": "❌ Cancel",
    },

    "btn_phone": {
        "ru": "📱 Отправить мой номер",
        "uz": "📱 Raqamimni yuborish",
        "en": "📱 Share my number",
    },

    "btn_open_instagram": {
        "ru": "📷 Открыть Instagram",
        "uz": "📷 Instagramni ochish",
        "en": "📷 Open Instagram",
    },

    "btn_open_channel": {
        "ru": "📢 Открыть канал",
        "uz": "📢 Kanalni ochish",
        "en": "📢 Open channel",
    },

    "channel_text": {
        "ru": "1️⃣ Откройте наш канал или Instagram и выберите десерты.\n2️⃣ Вернитесь сюда и нажмите «📝 Оставить заявку» — мы всё оформим и свяжемся с вами 👇",
        "uz": "1️⃣ Kanalimiz yoki Instagramni oching va shirinliklarni tanlang.\n2️⃣ Shu yerga qaytib «📝 Ariza qoldirish» tugmasini bosing — biz buyurtmani rasmiylashtirib, siz bilan bog'lanamiz 👇",
        "en": "1️⃣ Open our channel or Instagram and choose your desserts.\n2️⃣ Come back here and press “📝 Place an order” — we will arrange everything and contact you 👇",
    },

    "ask_items": {
        "ru": "Что вы хотите заказать? Напишите название десерта из канала и количество (например: Медовик, 1 шт.)",
        "uz": "Nimani buyurtma qilmoqchisiz? Kanaldagi shirinlik nomini va miqdorini yozing (masalan: Medovik, 1 dona)",
        "en": "What would you like to order? Write the dessert name from the channel and the quantity (e.g. Honey cake, 1 pc)",
    },

    "ask_name": {
        "ru": "Как к вам обращаться?",
        "uz": "Sizga qanday murojaat qilaylik?",
        "en": "What is your name?",
    },

    "ask_phone": {
        "ru": "Ваш номер телефона:",
        "uz": "Telefon raqamingiz:",
        "en": "Your phone number:",
    },

    "bad_phone": {
        "ru": "Пожалуйста, укажите корректный номер.",
        "uz": "Iltimos, to'g'ri raqam kiriting.",
        "en": "Please enter a valid phone number.",
    },

    "ask_date": {
        "ru": "На какую дату и время нужен заказ? (например, 25.10 в 15:00)\nУкажите также «самовывоз» или адрес доставки.",
        "uz": "Buyurtma qaysi sana va vaqtga kerak? (masalan, 25.10 soat 15:00)\nShuningdek, «olib ketish» yoki yetkazib berish manzilini yozing.",
        "en": "For what date and time do you need the order? (e.g. 25.10 at 15:00)\nAlso write \"pickup\" or your delivery address.",
    },

    "ask_comment": {
        "ru": "Пожелания к заказу (надпись на торте, аллергии)? Если нет — напишите «нет».",
        "uz": "Buyurtmaga istaklar (tortdagi yozuv, allergiya)? Yo'q bo'lsa — «yo'q» deb yozing.",
        "en": "Any special requests (cake inscription, allergies)? If none, write \"no\".",
    },

    "order_thanks": {
        "ru": "Спасибо! Заявка принята 🎉 Мы свяжемся с вами для подтверждения.",
        "uz": "Rahmat! Ariza qabul qilindi 🎉 Tasdiqlash uchun siz bilan bog'lanamiz.",
        "en": "Thank you! Your request has been received 🎉 We will contact you to confirm it.",
    },

    "cancelled": {
        "ru": "Отменено.",
        "uz": "Bekor qilindi.",
        "en": "Cancelled.",
    },

    "contacts": {
        "ru": (
            f"🍰 {SHOP_NAME}\n\n"
            f"📍 Адрес: {ADDRESS['ru']}\n"
            f"📞 Телефон: {PHONE}\n"
            "🕒 Приём заказов: ежедневно 8:00–22:00\n"
            "🚚 Самовывоз и доставка по городу\n"
            f"{link_lines('ru')}"
            f"🤖 Наш бот: {BOT_USERNAME}"
        ),

        "uz": (
            f"🍰 {SHOP_NAME}\n\n"
            f"📍 Manzil: {ADDRESS['uz']}\n"
            f"📞 Telefon: {PHONE}\n"
            "🕒 Buyurtmalar: har kuni 8:00–22:00\n"
            "🚚 Olib ketish va shahar bo'ylab yetkazib berish\n"
            f"{link_lines('uz')}"
            f"🤖 Bizning bot: {BOT_USERNAME}"
        ),

        "en": (
            f"🍰 {SHOP_NAME}\n\n"
            f"📍 Address: {ADDRESS['en']}\n"
            f"📞 Phone: {PHONE}\n"
            "🕒 Orders accepted: daily 8:00–22:00\n"
            "🚚 Pickup and city delivery\n"
            f"{link_lines('en')}"
            f"🤖 Our bot: {BOT_USERNAME}"
        ),
    },
}


# ======================= СОСТОЯНИЯ И ДАННЫЕ =======================

router = Router()

user_lang: dict[int, str] = {}


class Order(StatesGroup):
    items = State()
    name = State()
    phone = State()
    date = State()
    comment = State()


# ======================= ЯЗЫК =======================

def load_langs() -> dict[int, str]:
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return {
                int(k): v
                for k, v in json.load(f).items()
                if v in LANG_TITLES
            }
    except (FileNotFoundError, ValueError):
        return {}


def save_langs() -> None:
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(user_lang, f)
    except OSError:
        logging.exception("Не удалось сохранить языки пользователей")


def lang_of(uid: int) -> str:
    return user_lang.get(uid, "ru")


def t(uid: int, key: str) -> str:
    return TEXTS[key][lang_of(uid)]


def variants(key: str) -> set[str]:
    return set(TEXTS[key].values())


# ======================= КЛАВИАТУРЫ =======================

def lang_kb():
    kb = InlineKeyboardBuilder()

    for code, title in LANG_TITLES.items():
        kb.button(text=title, callback_data=f"lang:{code}")

    kb.adjust(1)
    return kb.as_markup()


def main_menu(uid: int):
    kb = ReplyKeyboardBuilder()

    for key in (
        "btn_channel",
        "btn_request",
        "btn_contacts",
        "btn_lang",
    ):
        kb.button(text=t(uid, key))

    kb.adjust(2, 2)

    return kb.as_markup(resize_keyboard=True)


def channel_kb(uid: int):
    kb = InlineKeyboardBuilder()

    if is_set(CHANNEL_URL):
        kb.button(
            text=t(uid, "btn_open_channel"),
            url=CHANNEL_URL,
        )

    if is_set(INSTAGRAM_URL):
        kb.button(
            text=t(uid, "btn_open_instagram"),
            url=INSTAGRAM_URL,
        )

    kb.button(
        text=t(uid, "btn_request"),
        callback_data="request",
    )

    kb.adjust(1)

    return kb.as_markup()


def cancel_kb(uid: int):
    kb = ReplyKeyboardBuilder()

    kb.button(text=t(uid, "btn_cancel"))

    return kb.as_markup(resize_keyboard=True)


def phone_kb(uid: int):
    kb = ReplyKeyboardBuilder()

    kb.button(
        text=t(uid, "btn_phone"),
        request_contact=True,
    )

    kb.button(text=t(uid, "btn_cancel"))

    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True)


# ======================= СТАРТ, ЯЗЫК, МЕНЮ =======================

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    uid = message.from_user.id

    if uid not in user_lang:
        await message.answer(
            CHOOSE_LANG,
            reply_markup=lang_kb(),
        )
        return

    await message.answer(
        t(uid, "welcome"),
        reply_markup=main_menu(uid),
    )


@router.message(F.text.in_(variants("btn_lang")))
@router.message(Command("lang"))
async def change_lang(message: Message):
    await message.answer(
        CHOOSE_LANG,
        reply_markup=lang_kb(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery, state: FSMContext):
    code = cb.data.split(":", 1)[1]

    if code not in LANG_TITLES:
        await cb.answer()
        return

    uid = cb.from_user.id

    user_lang[uid] = code

    save_langs()

    await state.clear()

    await cb.message.edit_text(
        f"✅ {LANG_TITLES[code]}"
    )

    await cb.message.answer(
        t(uid, "welcome"),
        reply_markup=main_menu(uid),
    )

    await cb.answer()


@router.message(F.text.in_(variants("btn_cancel")))
async def cancel(message: Message, state: FSMContext):
    await state.clear()

    uid = message.from_user.id

    await message.answer(
        t(uid, "cancelled"),
        reply_markup=main_menu(uid),
    )


@router.message(F.text.in_(variants("btn_channel")))
async def channel(message: Message):
    uid = message.from_user.id

    await message.answer(
        t(uid, "channel_text"),
        reply_markup=channel_kb(uid),
    )


@router.message(F.text.in_(variants("btn_contacts")))
async def contacts(message: Message):
    await message.answer(
        t(message.from_user.id, "contacts")
    )


# ======================= ЗАЯВКА =======================

@router.message(F.text.in_(variants("btn_request")))
async def request_start(
    message: Message,
    state: FSMContext,
):
    uid = message.from_user.id

    await state.set_state(Order.items)

    await message.answer(
        t(uid, "ask_items"),
        reply_markup=cancel_kb(uid),
    )


@router.callback_query(F.data == "request")
async def request_from_button(
    cb: CallbackQuery,
    state: FSMContext,
):
    uid = cb.from_user.id

    await state.set_state(Order.items)

    await cb.message.answer(
        t(uid, "ask_items"),
        reply_markup=cancel_kb(uid),
    )

    await cb.answer()


@router.message(Order.items, F.text)
async def order_items(
    message: Message,
    state: FSMContext,
):
    uid = message.from_user.id

    await state.update_data(
        items=message.text.strip()
    )

    await state.set_state(Order.name)

    await message.answer(
        t(uid, "ask_name")
    )


@router.message(Order.name, F.text)
async def order_name(
    message: Message,
    state: FSMContext,
):
    uid = message.from_user.id

    await state.update_data(
        name=message.text.strip()
    )

    await state.set_state(Order.phone)

    await message.answer(
        t(uid, "ask_phone"),
        reply_markup=phone_kb(uid),
    )


@router.message(Order.phone)
async def order_phone(
    message: Message,
    state: FSMContext,
):
    uid = message.from_user.id

    phone = (
        message.contact.phone_number
        if message.contact
        else (message.text or "").strip()
    )

    if len(phone) < 6:
        await message.answer(
            t(uid, "bad_phone")
        )
        return

    await state.update_data(phone=phone)

    await state.set_state(Order.date)

    await message.answer(
        t(uid, "ask_date"),
        reply_markup=cancel_kb(uid),
    )


@router.message(Order.date, F.text)
async def order_date(
    message: Message,
    state: FSMContext,
):
    uid = message.from_user.id

    await state.update_data(
        date=message.text.strip()
    )

    await state.set_state(Order.comment)

    await message.answer(
        t(uid, "ask_comment")
    )


@router.message(Order.comment, F.text)
async def order_done(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    await state.clear()

    user = message.from_user
    uid = user.id

    username = (
        f"@{user.username}"
        if user.username
        else "username не указан"
    )

    order = (
        "🆕 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"🛍 {html.escape(data['items'])}\n\n"
        f"👤 {html.escape(data['name'])}\n"
        f"🔗 Username: {html.escape(username)}\n"
        f"🆔 ID: <a href=\"tg://user?id={uid}\">{uid}</a> "
        "(нажмите, чтобы открыть профиль)\n"
        f"🌐 Язык клиента: "
        f"{html.escape(LANG_TITLES[lang_of(uid)])}\n"
        f"📞 {html.escape(data['phone'])}\n"
        f"🗓 {html.escape(data['date'])}\n"
        f"💬 {html.escape(message.text.strip())}"
    )

    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                order,
                parse_mode="HTML",
            )
        except Exception:
            logging.exception(
                "Не удалось отправить заявку администратору"
            )

    await message.answer(
        t(uid, "order_thanks"),
        reply_markup=main_menu(uid),
    )


# ======================= HTTP-СЕРВЕР ДЛЯ RENDER =======================

async def health(request):
    return web.Response(
        text="Mavluda Kitchen Bot is running!"
    )


async def start_http_server():
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(os.getenv("PORT", "10000"))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port,
    )

    await site.start()

    logging.info(
        f"HTTP server started on port {port}"
    )

    return runner


# ======================= ЗАПУСК =======================

async def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN не задан в переменных окружения!"
        )

    logging.basicConfig(
        level=logging.INFO
    )

    if not ADMIN_ID:
        logging.warning(
            "ADMIN_ID не задан: заявки не будут отправляться!"
        )

    user_lang.update(load_langs())

    runner = await start_http_server()

    bot = Bot(BOT_TOKEN)

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
