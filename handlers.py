import config

from models import User
from urllib.parse import urlparse, parse_qs

from api_functions import get_VK_token, get_target, find_target, send_msg
from vk_celery import process_friends, process_likes

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from magic_filter import F

bot = Bot(token=config.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def start(message: types.message):
    data = {'user_id': message.from_user.id}
    entry, is_new = User.get_or_create(
                user_id = message.from_user.id
            )
    if not is_new:
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    await message.answer('Привет, {name}. Мне для работы нужно получить от тебя токен ВК. \nВот инструкция как это сделать: \n{instruction_url}. \nКак посмотришь, то переходи по ссылке: \n{create_url}.\nКогда сделаешь настройки то нажми \n/authorize'.format(
        name=message.from_user.first_name,
        instruction_url = 'https://youtu.be/JT5QR5jHhVA',
        create_url = 'https://vk.com/editapp?act=create'
                         ))

@dp.message_handler(commands=['likes'])
async def likes(message: types.message):
    vk_token = get_VK_token(message.from_user.id)
    target = get_target(message.from_user.id)
    
    data = {}
    data['target'] = target
    data['vk_token'] = vk_token
    data['from_user_id'] = message.from_user.id
    data['chat_id'] = message.chat.id

    process_likes.apply_async(args=[data])
    
    return await message.answer('Процесс пощел! Как закончу - напишу результат')
    
@dp.message_handler(commands=['friends'])
async def friends(message: types.message):
    vk_token = get_VK_token(message.from_user.id)
    target = get_target(message.from_user.id)
    print(vk_token)
    
    data = {}
    data['target'] = target
    data['vk_token'] = vk_token
    data['from_user_id'] = message.from_user.id
    data['chat_id'] = message.chat.id

    process_friends.apply_async(args=[data])
    
    return await message.answer('Процесс пощел! Как закончу - напишу результат')
    
#Форма для token
class FormAuth(StatesGroup):
    app_id = State()
    app_secret = State()
    
# Форма для target
class FormTarget(StatesGroup):
    target = State()
    target_sex = State()

# Добавляем возможность отмены, если пользователь передумал заполнять
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('ОК')

#Клавиатура для action
inline_btn_1 = InlineKeyboardButton('Ставить лайки', callback_data='action_likes_btn')
inline_btn_2 = InlineKeyboardButton('Добавлять друзей', callback_data='action_friends_btn')
inline_btn_3 = InlineKeyboardButton('Делать все вместе', callback_data='action_all_btn')
inline_btn_4 = InlineKeyboardButton('Ничего не делать', callback_data='action_none_btn')
inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4)
   
# Указать поведение
@dp.message_handler(commands=['action'])
async def action(message: types.Message):
    await message.answer('Что мне делать?', reply_markup=inline_kb1)
    
@dp.callback_query_handler(lambda c: c.data == 'action_likes_btn')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'do_likes': True}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()

@dp.callback_query_handler(lambda c: c.data == 'action_friends_btn')
async def process_callback_button2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'do_friends': True}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()
    
@dp.callback_query_handler(lambda c: c.data == 'action_all_btn')
async def process_callback_button3(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'do_friends': True,
            'do_likes': True}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()

@dp.callback_query_handler(lambda c: c.data == 'action_none_btn')
async def process_callback_button4(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'do_friends': False,
            'do_likes': False}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()

#Клавиатура для target_sex    
inline_sex_btn_1 = InlineKeyboardButton('Женский', callback_data='female_btn')
inline_sex_btn_2 = InlineKeyboardButton('Мужской', callback_data='male_btn')
inline_sex_btn_3 = InlineKeyboardButton('Всех', callback_data='allsex_btn')
inline_sex_kb = InlineKeyboardMarkup().add(inline_sex_btn_1, inline_sex_btn_2, inline_sex_btn_3)

#Принимаем таргет и пол
@dp.message_handler(commands=['target'])
async def target(message: types.Message):
    await FormTarget.target.set()
    await message.reply('Отправь ссылку на пользователя или сообщество ВК')
    
# Сюда приходит ответ с target
@dp.message_handler(state=FormTarget.target)
async def process_target(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        token = get_VK_token(message.from_user.id)
        url = urlparse(message.text).path[1:]
        target = find_target(url, token)
        
        print(target)
        data = {'target': target}
        entry, is_new = User.get_or_create(
                user_id = message.from_user.id
            )
        if not is_new:
            query = User.update(data).where(User.user_id==message.from_user.id)
            query.execute()
    entry = User.get(user_id = message.from_user.id)
    await message.answer('Цель принята! Какого пола будем добавлять друзей?\n', reply_markup=inline_sex_kb)
    await state.finish()
    #await FormTarget.next()   

#Ловим target_sex
@dp.callback_query_handler(lambda c: c.data == 'female_btn')
async def process_callback_female(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'target_sex': 1}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()
    print(entry.target_sex)
    send_msg(user_id, 'Принято! ')

#Ловим target_sex
@dp.callback_query_handler(lambda c: c.data == 'male_btn')
async def process_callback_male(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'target_sex': 2}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()
    print(entry.target_sex)

#Ловим target_sex    
@dp.callback_query_handler(lambda c: c.data == 'allsex_btn')
async def process_callback_allsex(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = {'target_sex': 3}
    entry, is_new = User.get_or_create(
            user_id = user_id
        )
    query = User.update(data).where(User.user_id==user_id)
    query.execute()
    print(entry.target_sex)
    

# Начинаем наш диалог authorize
@dp.message_handler(commands=['authorize'])
async def authorize(message: types.Message):
    await FormAuth.app_id.set()
    await message.reply("Привет! Укажи id вашего приложения.")

# Сюда приходит ответ с appid
@dp.message_handler(state=FormAuth.app_id)
async def process_app_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data = {'app_id': message.text}
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    url = 'https://oauth.vk.com/authorize?client_id={app_id}&display=mobile&redirect_uri={redirect_url}/vkcreds/{app_id}&scope=offline,wall,photos,groups,docs,friends,stories,notifications&response_type=token&v=5.131'.format(
        app_id = message.text,
        redirect_url = config.REDIRECT_URL
    )
    await FormAuth.next()
    await message.answer('ID принят! Теперь перейди по ссылке: ')
    await message.answer(url)

#Парсим токен и записываем в базу    
@dp.message_handler(state=FormAuth.app_secret)
async def process_app_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        pq = parse_qs(urlparse(message.text).fragment)
        data = {'token': pq["access_token"][0]}
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    entry = User.get(user_id = message.from_user.id)
    
    await message.answer('Секретный ключ принят! Теперь нужно добавить ссылку на цель в ВК с помощью команды \n/target')
    await state.finish()
    

