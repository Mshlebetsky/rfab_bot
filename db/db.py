from __future__ import annotations
import json
import sqlite3
from typing import List, Optional, Tuple, Dict
import logging
import os
# DB_PATH = 'db/menu_bot.db'
DB_PATH = '/app/data/menu_bot.db'

MENU_JSON_PATH = 'menu/menu.json'  # optional path for import


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------- DATABASE ---------------------------

SCHEMA = '''
PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS menu_nodes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
parent_id INTEGER REFERENCES menu_nodes(id) ON DELETE CASCADE,
title TEXT NOT NULL,
slug TEXT, -- nullable: if not null, points to an item in items.slug
sort_order INTEGER DEFAULT 0,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE UNIQUE INDEX IF NOT EXISTS idx_menu_nodes_slug ON menu_nodes(slug) WHERE slug IS NOT NULL;


CREATE TABLE IF NOT EXISTS items (
slug TEXT PRIMARY KEY,
title TEXT NOT NULL,
content TEXT NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys for SQLite
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()
    logger.info('Database initialized (%s)', DB_PATH)

# --------------------------- IMPORTER: JSON -> DB ---------------------------
# The provided menu.json format: nested dicts where leaf values are slugs (item keys)


def insert_item_if_not_exists(conn: sqlite3.Connection, slug: str, title_hint: Optional[str] = None):
    cur = conn.cursor()
    cur.execute('SELECT slug FROM items WHERE slug = ?', (slug,))
    if cur.fetchone():
        return
    title = title_hint or slug
    content = f"Пустой контент для {slug} — заполните в админ панели."
    cur.execute('INSERT INTO items(slug, title, content) VALUES (?,?,?)', (slug, title, content))
    conn.commit()


def import_menu_json(path: str = MENU_JSON_PATH):
    """Recursively import menu.json into menu_nodes and items."""
    if not os.path.exists(path):
        logger.warning('Menu JSON not found: %s', path)
        return

    with open(path, 'r', encoding='utf-8') as f:
        menu = json.load(f)

    conn = get_conn()
    cur = conn.cursor()

    # Очищаем таблицы перед повторным импортом
    cur.execute("DELETE FROM menu_nodes")
    cur.execute("DELETE FROM items")
    conn.commit()

    def _insert_node(parent_id: Optional[int], title: str, value):
        """
        value = либо строка (slug), либо словарь (вложенные подразделы)
        """

        # --- 1. value == slug (строка)
        if isinstance(value, str):
            slug = value

            # создаём item если нет
            insert_item_if_not_exists(conn, slug, title)

            # проверяем, есть ли уже узел с этим slug
            cur.execute("SELECT id FROM menu_nodes WHERE slug = ?", (slug,))
            row = cur.fetchone()
            if row:
                # просто создаём новый подкатегорийный узел, но без slug
                # чтобы избежать дублей
                cur.execute(
                    'INSERT INTO menu_nodes(parent_id, title, slug) VALUES (?,?,NULL)',
                    (parent_id, title)
                )
                return cur.lastrowid

            # вставляем leaf-узел с этим slug
            cur.execute(
                'INSERT INTO menu_nodes(parent_id, title, slug) VALUES (?,?,?)',
                (parent_id, title, slug)
            )
            return cur.lastrowid

        # --- 2. value == dict (подкатегория)
        cur.execute(
            'INSERT INTO menu_nodes(parent_id, title, slug) VALUES (?,?,NULL)',
            (parent_id, title)
        )
        this_id = cur.lastrowid

        for child_title, child_value in value.items():
            _insert_node(this_id, child_title, child_value)

        return this_id

    # top-level
    for root_title, root_val in menu.items():
        _insert_node(None, root_title, root_val)

    conn.commit()
    conn.close()
    logger.info('Imported menu.json into DB')


# --------------------------- DB HELPERS ---------------------------

def get_children(parent_id: Optional[int]) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    if parent_id is None:
        cur.execute('SELECT id, title, slug FROM menu_nodes WHERE parent_id IS NULL ORDER BY sort_order, id')
    else:
        cur.execute('SELECT id, title, slug FROM menu_nodes WHERE parent_id = ? ORDER BY sort_order, id', (parent_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_node(node_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM menu_nodes WHERE id = ?', (node_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_item(slug: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM items WHERE slug = ?', (slug,))
    row = cur.fetchone()
    conn.close()
    return row