from __future__ import annotations
import sqlite3
from typing import List, Optional
import logging
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.db import get_children, get_node, get_item
import re




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def esc_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)
# --------------------------- MENU MARKUP GENERATOR ---------------------------

def build_menu_markup(nodes: List[sqlite3.Row], include_back: bool = False,
                      back_to: Optional[int] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # добавляем кнопки меню
    for node in nodes:
        builder.button(text=node['title'], callback_data=f'menu:{node["id"]}')

    # расположение по 2 кнопки в строке
    builder.adjust(2)

    # добавляем кнопку "Назад" на отдельной строке
    if include_back:
        if back_to is None:
            builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:root'))
        else:
            builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data=f'menu:{back_to}'))

    return builder.as_markup()


menu_router = Router()


@menu_router.message(Command(commands=['start']))
async def cmd_start(message: types.Message):
    # show top-level menu
    nodes = get_children(None)
    markup = build_menu_markup(nodes)
    await message.answer('Главное меню:', reply_markup=markup)


@menu_router.callback_query(lambda c: c.data and c.data.startswith('menu:'))
async def callback_menu(cb: types.CallbackQuery):
    data = cb.data

    # special root token
    if data == 'menu:root':
        parent_id = None
    else:
        node_id = int(data.split(':', 1)[1])
        node = get_node(node_id)

        if node is None:
            await cb.answer('Узел не найден', show_alert=True)
            return

        # If node has a slug -> show item
        if node['slug']:
            item = get_item(node['slug'])
            if item:
                text = f"<b>{item['title']}</b>\n\n{item['content']}"
                # safe_text = esc_md(text)
                await cb.message.edit_text(text, parse_mode='HTML')
                return
            else:
                await cb.message.edit_text('Контент отсутствует. Админ может добавить его через /admin.')
                return

        # else show children
        parent_id = node_id

    # fetch children
    children = get_children(parent_id)
    if not children:
        await cb.message.edit_text('Пустой раздел.')
        return

    # determine back button
    if parent_id is None:
        # we are in root → back is NOT needed
        include_back = False
        back_to = None
    else:
        # we are inside → show back button
        include_back = True
        parent_node = get_node(parent_id)
        back_to = parent_node['parent_id'] if parent_node else None

    markup = build_menu_markup(children, include_back=include_back, back_to=back_to)
    await cb.message.edit_text('Выберите пункт:', reply_markup=markup)


