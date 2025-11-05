import logging
from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from kb.kb_menu import build_keyboard, menu_paths
from scripts.helper import readMenu, readData, fill_menu, get_menu_level

logger = logging.getLogger(__name__)
menu_router = Router()

# Загружаем меню и тексты
menu_json = readMenu()
data_json = readData()
menu = fill_menu(menu_json, data_json)


# === /start ===
@menu_router.message(CommandStart())
async def start_message(message: types.Message):
    await message.answer("Выберите раздел:", reply_markup=build_keyboard(menu))


# === Обработка нажатий ===
@menu_router.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data

    # Кнопка "назад"
    if data.startswith("back_"):
        back_hash = data.replace("back_", "")
        parent_path = None
        for full_path in menu_paths.values():
            if abs(hash(full_path)) == int(back_hash):
                parts = full_path.split(">")
                parent_path = ">".join(parts[:-1])
                break
        level = get_menu_level(menu, parent_path)
        text = "Выберите раздел:" if not parent_path else f"Раздел: {parts[-2]}"
        await callback.message.edit_text(text, reply_markup=build_keyboard(level, parent_path))
        return
    # Кнопка Главное меню
    if data == "back_":  # пустой hash
        await callback.message.edit_text(
            "Выберите раздел:",
            reply_markup=build_keyboard(menu)
        )
        return
    # Обычная кнопка
    full_path = menu_paths.get(data)
    if not full_path:
        await callback.answer("Ошибка: пункт не найден", show_alert=True)
        return

    level = get_menu_level(menu, full_path)
    if isinstance(level, dict):  # есть подменю
        await callback.message.edit_text(f"Раздел: {full_path.split('>')[-1]}", reply_markup=build_keyboard(level, full_path))
    else:
        await callback.message.edit_text(
            f"<b>{full_path.split('>')[-1]}</b>\n\n{level}",
            parse_mode="HTML",
            reply_markup=build_keyboard({}, path=full_path, add_main=True)  # пустой dict + кнопка "Главное меню"
        )
