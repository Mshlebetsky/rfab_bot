import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery

from kb.kb_menu  import build_keyboard
from scripts.helper import readMenu, readData, get_menu_level, is_final_value

logger = logging.getLogger(__name__)
menu_router = Router()

menu_json = readMenu()
data_json = readData()
user_paths = {}  # user_id -> путь (список ключей)

def format_breadcrumbs(path_list: list[str]) -> str:
    """Создаёт красивую строку вида 'FAQ → Начало игры'"""
    if not path_list:
        return "📜 Главное меню"
    return "🧭 " + " → ".join(path_list)

@menu_router.message(CommandStart())
async def start_menu(msg: types.Message):
    user_paths[msg.from_user.id] = []
    root = menu_json
    keyboard = build_keyboard(root, [])
    await msg.answer(format_breadcrumbs([]), reply_markup=keyboard)

@menu_router.callback_query(F.data)
async def navigate_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    # Назад
    if data == "BACK":
        if user_id in user_paths and user_paths[user_id]:
            user_paths[user_id].pop()
        current_level = get_menu_level(menu_json, user_paths[user_id])
        keyboard = build_keyboard(current_level, user_paths[user_id])
        await callback.message.edit_text(
            format_breadcrumbs(user_paths[user_id]), reply_markup=keyboard
        )
        await callback.answer()
        return

    path_list = data.split(">")
    current_level = get_menu_level(menu_json, path_list)

    if current_level is None:
        await callback.answer("Ошибка пути", show_alert=True)
        return

    user_paths[user_id] = path_list

    if is_final_value(current_level):
        key = current_level
        text = data_json.get(key, f"❌ Текст для '{key}' не найден.")
        breadcrumb = format_breadcrumbs(path_list)
        await callback.message.edit_text(
            f"{breadcrumb}\n\n{text}",
            reply_markup=build_keyboard({}, path_list)
        )
    else:
        keyboard = build_keyboard(current_level, path_list)
        await callback.message.edit_text(
            format_breadcrumbs(path_list),
            reply_markup=keyboard
        )

    await callback.answer()
