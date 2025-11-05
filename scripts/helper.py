import json

def readMenu(path="menu/menu.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def readData(path="db/data.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_menu_level(menu, path_list):
    """Возвращает текущий уровень меню по пути"""
    current = menu
    for key in path_list:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def is_final_value(node):
    """Проверяет, является ли значение финальным (строка)"""
    return isinstance(node, str)
