from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

'''def build_keyboard(menu_level: dict, path: str = "") -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для текущего уровня меню.
    path — строка пути (например: "Экипировка>Кольца Амулеты Маски")
    """
    builder = InlineKeyboardBuilder()

    for key, value in menu_level.items():
        # Кодируем путь к элементу
        new_path = f"{path}>{key}" if path else key
        # Telegram не примет >64 байт, сокращаем через hash
        short_id = str(abs(hash(new_path)))[:20]
        builder.button(text=key, callback_data=short_id)
        menu_paths[short_id] = new_path  # глобальная карта путей

    if path:
        builder.button(text="⬅ Назад", callback_data="back_" + str(abs(hash(path)))[:20])

    builder.adjust(2)
    return builder.as_markup()

# Глобальный словарь для соответствия hash → реальный путь'''


def build_keyboard(menu_level: dict, path: str = "", add_main=False) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для текущего уровня меню.
    path — строка пути (например: "Экипировка>Кольца Амулеты Маски")
    add_main — добавить кнопку '🏠 Главное меню' для текста
    """
    builder = InlineKeyboardBuilder()

    for key, value in menu_level.items():
        new_path = f"{path}>{key}" if path else key
        short_id = str(abs(hash(new_path)))[:20]
        builder.button(text=key, callback_data=short_id)
        menu_paths[short_id] = new_path

    if path:
        # кнопка "Назад"
        builder.button(text="⬅ Назад", callback_data="back_" + str(abs(hash(path)))[:20])

    if add_main:
        builder.button(text="🏠 Главное меню", callback_data="back_")  # пустой hash → главная

    builder.adjust(2)
    return builder.as_markup()


menu_paths = {}
