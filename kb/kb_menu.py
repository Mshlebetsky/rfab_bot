from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_keyboard(menu_level, path):
    keyboard = []
    row = []
    if isinstance(menu_level, dict):
        for i, key in enumerate(menu_level.keys(), start=1):
            new_path = path + [key]
            row.append(
                InlineKeyboardButton(text=key, callback_data=">".join(new_path))
            )
            if i % 2 == 0:  # каждые 2 кнопки — новая строка
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
    if path:  # кнопка Назад
        keyboard.append([InlineKeyboardButton(text="⬅ Назад", callback_data="BACK")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
