from __future__ import annotations
import logging
from aiogram import types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import get_children, get_node, get_item, import_menu_json, get_conn, init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


admin_router = Router()


# Simple FSM states for admin flows
class AdminStates(StatesGroup):
    adding_category = State()
    adding_item_slug = State()
    adding_item_content = State()
    editing_node_title = State()
    editing_item_content = State()
    search_item = State()


ADMIN_USER_IDS = {435946390}  # replace with actual Telegram user ids of admins

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS



@admin_router.message(Command(commands=['admin']))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer('Доступ только для администраторов')
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Управление меню', callback_data='adm:manage_menu')],
        [InlineKeyboardButton(text='Управление товарами', callback_data='adm:manage_items')],
        [InlineKeyboardButton(text='Импорт menu.json', callback_data='adm:import_json')],
    ])
    await message.answer('Панель администратора', reply_markup=kb)


# --------------------------- ADMIN CALLBACKS ---------------------------

@admin_router.callback_query(lambda c: c.data and c.data.startswith('adm:'))
async def callback_admin(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer('Доступ запрещён', show_alert=True)
        return
    data = cb.data
    if data == 'adm:manage_menu':
        # Show top-level nodes with admin buttons
        nodes = get_children(None)
        builder = InlineKeyboardBuilder()

        for n in nodes:
            builder.row(
                InlineKeyboardButton(
                    text=n['title'],
                    callback_data=f"adm:node:{n['id']}"
                )
            )

        builder.row(
            InlineKeyboardButton(
                text='➕ Добавить root категорию',
                callback_data='adm:add_root'
            )
        )

        await cb.message.edit_text('Управление меню — корень', reply_markup=builder.as_markup())

        return
    if data == 'adm:import_json':
        import_menu_json()
        await cb.answer('Импорт завершён', show_alert=False)
        await cb.message.edit_text('Импортирован menu.json')
        return
    if data == 'adm:manage_items':
        await state.set_state(AdminStates.search_item)
        await cb.message.edit_text("Введите часть названия итема (регистр учитывается)")
        return


    # node specific actions
    if data.startswith('adm:node:'):
        node_id = int(data.split(':', 2)[2])
        node = get_node(node_id)
        if not node:
            await cb.answer('Узел не найден', show_alert=True)
            return
        text = f"Узел: {node['title']} (id={node['id']})\nslug={node['slug']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Переименовать', callback_data=f'adm:node_rename:{node_id}')],
            [InlineKeyboardButton(text='➕ Добавить подузел', callback_data=f'adm:node_add:{node_id}')],
            [InlineKeyboardButton(text='🔗 Привязать/сменить slug', callback_data=f'adm:node_setslug:{node_id}')],
            [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'adm:node_del:{node_id}')],
            [InlineKeyboardButton(text='Назад', callback_data='adm:manage_menu')]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
        return

    if data.startswith('adm:item:'):
        # show item edit options
        slug = data.split(':', 2)[2]
        item = get_item(slug)
        if not item:
            await cb.answer('Товар не найден', show_alert=True)
            return
        text = f"Товар: {item['title']}\nslug: {item['slug']}\n\n{item['content'][:200]}..."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Редактировать контент', callback_data=f'adm:item_edit:{slug}')],
            [InlineKeyboardButton(text='🗑 Удалить товар', callback_data=f'adm:item_del:{slug}')],
            [InlineKeyboardButton(text='Назад', callback_data='adm:manage_items')]
        ])
        await cb.message.edit_text(text, reply_markup=kb)
        return

    # node add/rename/del flows (kick to FSM or direct actions)
    if data.startswith('adm:node_add:'):
        parent_id = int(data.split(':', 2)[2])
        await state.update_data(admin_action='add_node', parent_id=parent_id)
        await state.set_state(AdminStates.adding_category)
        await cb.message.answer('Введите название новой подкатегории:')
        return

    if data == 'adm:add_root':
        await state.update_data(admin_action='add_node', parent_id=None)
        await state.set_state(AdminStates.adding_category)
        await cb.message.answer('Введите название новой root категории:')
        return

    if data.startswith('adm:node_rename:'):
        node_id = int(data.split(':', 2)[2])
        await state.update_data(admin_action='rename_node', node_id=node_id)
        await state.set_state(AdminStates.editing_node_title)

        await cb.message.answer('Введите новый заголовок для узла:')
        return

    if data.startswith('adm:node_del:'):
        node_id = int(data.split(':', 2)[2])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM menu_nodes WHERE id = ?', (node_id,))
        conn.commit()
        conn.close()
        await cb.answer('Узел удалён', show_alert=False)
        await cb.message.edit_text('Узел удалён. Обновите админ-панель', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('Обновить', callback_data='adm:manage_menu')]]))
        return

    if data.startswith('adm:node_setslug:'):
        node_id = int(data.split(':', 2)[2])
        await state.update_data(admin_action='set_slug', node_id=node_id)
        await state.set_state(AdminStates.adding_item_slug)

        await cb.message.answer('Введите slug to привязать (например: exp_system). Введите пустую строку чтобы отвязать.')
        return

    if data == 'adm:item_add':
        await state.update_data(admin_action='add_item')
        await state.set_state(AdminStates.adding_item_slug)

        await cb.message.answer('Введите slug для нового товара (латинскими, например: my_slug):')
        return

    if data.startswith('adm:item_edit:'):
        slug = data.split(':', 2)[2]
        await state.update_data(admin_action='edit_item', slug=slug)
        await state.set_state(AdminStates.editing_item_content)
        await cb.message.answer('Отправьте новый контент (Markdown) для товара:')
        return

    if data.startswith('adm:item_del:'):
        slug = data.split(':', 2)[2]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM items WHERE slug = ?', (slug,))
        # Also remove slug references in menu_nodes
        cur.execute('UPDATE menu_nodes SET slug = NULL WHERE slug = ?', (slug,))
        conn.commit()
        conn.close()
        await cb.answer('Товар удалён', show_alert=False)
        await cb.message.edit_text('Товар удалён. Обновите список', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('Обновить', callback_data='adm:manage_items')]]))
        return

    await cb.answer('Неизвестная админ-команда', show_alert=True)



# --------------------------- ADMIN FSM HANDLERS ---------------------------

@admin_router.message(AdminStates.adding_category)
async def process_add_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    parent_id = data.get('parent_id')
    title = message.text.strip()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO menu_nodes(parent_id, title) VALUES (?,?)', (parent_id, title))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer(f'Категория "{title}" добавлена.')


@admin_router.message(AdminStates.adding_item_slug)
async def process_add_item_slug(message: types.Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    action = data.get('admin_action')
    if action == 'add_item':
        slug = text
        # create item placeholder
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO items(slug, title, content) VALUES (?,?,?)', (slug, slug, f'Пустой контент для {slug}'))
        conn.commit()
        conn.close()
        await state.clear()
        await message.answer(f'Товар {slug} создан. Редактируйте контент через /admin -> Управление товарами')
        return

    if action == 'set_slug':
        node_id = data.get('node_id')
        slug = text if text else None
        conn = get_conn()
        cur = conn.cursor()
        if slug:
            # ensure item exists
            cur.execute('INSERT OR IGNORE INTO items(slug, title, content) VALUES (?,?,?)', (slug, slug, f'Пустой контент для {slug}'))
            cur.execute('UPDATE menu_nodes SET slug = ? WHERE id = ?', (slug, node_id))
            conn.commit()
            conn.close()
            await state.clear()
            await message.answer(f'Узел {node_id} привязан к {slug}')
            return
        else:
            cur.execute('UPDATE menu_nodes SET slug = NULL WHERE id = ?', (node_id,))
            conn.commit()
            conn.close()
            await state.clear()
            await message.answer(f'Узел {node_id} отвязан от товара')
            return

    await message.answer('Неизвестное действие')


@admin_router.message(AdminStates.editing_node_title)
async def process_rename_node(message: types.Message, state: FSMContext):
    data = await state.get_data()
    node_id = data.get('node_id')
    new_title = message.text.strip()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE menu_nodes SET title = ? WHERE id = ?', (new_title, node_id))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer('Узел переименован')


@admin_router.message(AdminStates.editing_item_content)
async def process_edit_item_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    slug = data.get('slug')
    content = message.text
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE items SET content = ?, title = ? WHERE slug = ?', (content, content.split('\n',1)[0] if content else slug, slug))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer('Контент товара обновлён')


@admin_router.message(AdminStates.search_item)
async def process_item_search(message: types.Message, state: FSMContext):
    query = message.text.strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT slug, title FROM items
        WHERE slug LIKE ? COLLATE NOCASE
           OR title LIKE ? COLLATE NOCASE
        ORDER BY created_at DESC
        LIMIT 50
    """, (f"%{query}%", f"%{query}%"))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await message.answer("❌ Ничего не найдено. Введите другой запрос:")
        return

    kb = InlineKeyboardBuilder()

    for r in rows:
        kb.row(
            InlineKeyboardButton(
                text=f"{r['title']} ({r['slug']})",
                callback_data=f"adm:item:{r['slug']}"
            )
        )

    kb.row(
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="adm:manage_items")
    )

    await state.clear()
    await message.answer("Результаты поиска:", reply_markup=kb.as_markup())
