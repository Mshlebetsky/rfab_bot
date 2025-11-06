import hashlib

path_map = {}

def register_path(path_list):
    """Создаёт короткий hash для callback_data и сохраняет соответствие"""
    path_str = ">".join(path_list)
    hash_id = hashlib.md5(path_str.encode()).hexdigest()[:10]
    path_map[hash_id] = path_list
    return hash_id
