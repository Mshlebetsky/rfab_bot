from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.path_manager import register_path  # ✅ теперь безопасно

def build_keyboard(menu_level, path):
    keyboard = []
    row = []

    # Основные кнопки
    if isinstance(menu_level, dict):
        for i, key in enumerate(menu_level.keys(), start=1):
            new_path = path + [key]
            hash_id = register_path(new_path)  # генерируем короткий id
            row.append(InlineKeyboardButton(text=key, callback_data=hash_id))
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    # Если это не корень — добавить кнопку "Назад"
    if path:
        keyboard.append([InlineKeyboardButton(text="⬅ Назад", callback_data="BACK")])
    else:
        # ✅ если это корень — добавить кнопку-ссылку
        keyboard.append([
            InlineKeyboardButton(
                text="🎧 Наш Discord сервер",
                url="https://discord.gg/AFRBWyCu"  # ← поставь сюда свою ссылку
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
