import json
import os

def read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def readMenu():
    return read_json("menu/menu.json")

def readData():
    return read_json("db/data.json")

def fill_menu(menu: dict, data: dict):
    """
    Рекурсивно заменяет пустые строки на тексты из data.json (если есть),
    а вложенные dict оставляет как есть.
    """
    result = {}
    for key, value in menu.items():
        if isinstance(value, dict):
            result[key] = fill_menu(value, data)
        elif value == "":
            # Если текст есть в data.json, вставляем его
            result[key] = data.get(key, f"Нет данных для '{key}'")
        else:
            result[key] = value
    return result


def get_menu_level(menu_dict, path: str):
    """Рекурсивно достаёт уровень меню по пути 'A>B>C'."""
    if not path:
        return menu_dict
    parts = path.split(">")
    node = menu_dict
    for part in parts:
        node = node.get(part.strip(), {})
    return node
