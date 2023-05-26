import config
import time
import requests
import datetime
from models import User, Friend
from urllib.parse import urlparse, urlsplit


from urllib.parse import urlparse, urldefrag, parse_qs
#from handlers import *
from celery import Celery
from celery.schedules import crontab
#from api_operator import client


from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from magic_filter import F

import vk_captchasolver as vc

bot = Bot(token=config.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

client = Celery('vk_like', broker=config.CELERY_BROKER_URL)
client.conf.result_backend = config.CELERY_RESULT_BACKEND
client.conf.timezone = 'Europe/Moscow'


client.conf.beat_schedule = {
    'cron_friends': {
        'task': 'handlers.cron_friends',
        'schedule': crontab(hour=10, minute=00)
    },
    'cron_likes': {
        'task': 'handlers.cron_likes',
        'schedule': crontab(hour=10, minute=57)
    }
}

@client.task
def cron_friends():
    users = User.select()
    for user in users:
        vk_token = get_VK_token(user.user_id)
        target = get_target(user.user_id)
        print(vk_token)
        
        data = {}
        data['target'] = target
        data['vk_token'] = vk_token
        data['from_user_id'] = user.user_id
        data['chat_id'] = user.user_id
        send_msg(user.user_id, 'Пощел искать друзей!')
        process_friends.apply_async(args=[data])

@client.task
def cron_likes():
    users = User.select()
    for user in users:
        vk_token = get_VK_token(user.user_id)
        print(vk_token)
        
        data = {}
        
        data['vk_token'] = vk_token
        data['from_user_id'] = user.user_id
        data['chat_id'] = user.user_id
        send_msg(user.user_id, 'Пошел ставить лайки!')
        process_likes.apply_async(args=[data])

@dp.message_handler(commands=['start'])
async def start(message: types.message):
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
    
# создаём форму и указываем поля
class Form(StatesGroup):
    target = State()
    token = State()

class FormAuth(StatesGroup):
    app_id = State()
    app_secret = State()
    
@dp.message_handler(commands=['target'])
async def target(message: types.Message):

    await Form.target.set()
    await message.reply("Привет! Укажи цель.")

# Добавляем возможность отмены, если пользователь передумал заполнять
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('ОК')

def find_target(url, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }

    result = requests.get(
        #'{api_uri}users.search?q={q}&v={ver}'.format(
        '{api_uri}groups.getById?group_id={q}&v={ver}'.format(
        api_uri = config.API_URL, 
        q = url,
        ver = config.API_VERSION), headers=newheaders).json()
    #print(result)
    try:
        if result['response'][0]['id'] != []:
            return result['response'][0]['id']
    except:
        pass
        
    result = requests.get(
        '{api_uri}users.get?user_ids={q}&v={ver}'.format(
        api_uri = config.API_URL, 
        q = url,
        ver = config.API_VERSION), headers=newheaders).json()
    #print(result)
    try:
        if result['response'][0]['id'] != []:
            return result['response'][0]['id']
    except:
        pass
    
    return result
    
    return vk_target
# Сюда приходит ответ с target
@dp.message_handler(state=Form.target)
async def process_target(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        token = get_VK_token(message.from_user.id)
        #target = find_target(message.text, token)['response']['items'][0]['id']
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
    await message.answer('Цель принята!')

    await state.finish()
    
# Начинаем наш диалог
@dp.message_handler(commands=['token'])
async def token(message: types.Message):
    await Form.token.set()
    await message.reply("Привет! Укажи токен ВК.")

# Сюда приходит ответ с именем
@dp.message_handler(state=Form.token)
async def process_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data = {'token': message.text}
        entry, is_new = User.get_or_create(
                user_id = message.from_user.id
            )
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    entry = User.get(user_id = message.from_user.id)
    await message.answer('Токен принят!')

    await state.finish()
    
# Начинаем наш диалог authorize
@dp.message_handler(commands=['authorize'])
async def authorize(message: types.Message):
    await FormAuth.app_id.set()
    await message.reply("Привет! Укажи id вашего приложения.")

# Сюда приходит ответ с appid
@dp.message_handler(state=FormAuth.app_id)
async def process_app_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        '''
        data = {'app_id': message.text}
        entry, is_new = User.get_or_create(
                user_id = message.from_user.id,
                app_id = message.text
            )
        if not is_new:
            query = User.update(data).where(User.user_id==message.from_user.id)
            query.execute()
        '''
        data = {'app_id': message.text}
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    url = 'https://oauth.vk.com/authorize?client_id={app_id}&display=mobile&redirect_uri={redirect_url}/vkcreds/{app_id}&scope=offline,wall,photos,groups,docs,friends,stories,notifications&response_type=token&v=5.131'.format(
        app_id = message.text,
        redirect_url = config.REDIRECT_URL
    )
    #entry = User.get(user_id = message.from_user.id)
    await FormAuth.next()
    await message.answer(url)
    await message.answer('ID принят! Теперь укажи секретный ключ')
    
@dp.message_handler(state=FormAuth.app_secret)
async def process_app_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        '''
        data = {'app_secret': message.text}
        entry, is_new = User.get_or_create(
                user_id = message.from_user.id,
                app_secret = message.text
            )
        if not is_new:
            query = User.update(data).where(User.user_id==message.from_user.id)
            query.execute()
        '''
        pq = parse_qs(urlparse(message.text).fragment)
        data = {'token': pq["access_token"][0]}
        query = User.update(data).where(User.user_id==message.from_user.id)
        query.execute()
    entry = User.get(user_id = message.from_user.id)
    
    await message.answer('Секретный ключ принят! Token: ' + entry.token)
    await state.finish()
    

def get_VK_token(user_id):
    query = User.get(user_id = user_id)
    return query.token

def get_target(user_id):
    query = User.get(user_id = user_id)
    return query.target


def get_wall(id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get('{api_uri}wall.get?owner_id={owner_id}&v={ver}'.format(
        api_uri=config.API_URL, owner_id=id, ver=config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            #print(result)
            return result['error']['error_code']
    return result

def get_likes(type, owner_id, item_id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}likes.getList?type={type}&owner_id={owner_id}&item_id={item_id}&v={ver}'.format(
        api_uri = config.API_URL, 
        type = type, 
        owner_id = owner_id,
        item_id = item_id, 
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result

def are_we_friends(user_id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}friends.areFriends?user_ids={user_id}&v={ver}'.format(
        api_uri = config.API_URL, 
        user_id = user_id,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result

def get_users(user_ids, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}users.get?user_ids={user_ids}&v={ver}&fields=sex,bdate'.format(
        api_uri = config.API_URL, 
        user_ids= user_ids,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result

def add_friend(user_id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}friends.add?user_id={user_id}&v={ver}'.format(
        api_uri = config.API_URL, 
        user_id= user_id,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    if 'response' in result.keys():
        return result['response']
    return result

def is_liked(type, owner_id, item_id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }

    result = requests.get(
        '{api_uri}likes.isLiked?type={type}&owner_id={owner_id}&item_id={item_id}&v={ver}'.format(
        api_uri = config.API_URL, 
        type = type,
        item_id = item_id,
        owner_id= owner_id,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result

def add_like(type, owner_id, item_id, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}likes.add?type={type}&owner_id={owner_id}&item_id={item_id}&v={ver}'.format(
        api_uri = config.API_URL, 
        type = type,
        owner_id = owner_id,
        item_id = item_id,
        ver = config.API_VERSION), headers=newheaders).json()
    
    if 'error' in result.keys():
        #print(result)
        if result['error']['error_code'] == 14:
            captcha_key = vc.solve(sid=result['error']['captcha_sid'])
            #print(result['error']['captcha_img'])
            #print(captcha_key)
            result = requests.get(
                '{api_uri}likes.add?type={type}&owner_id={owner_id}&item_id={item_id}&captcha_sid={sid}&captcha_key={key}&v={ver}'.format(
                api_uri = config.API_URL, 
                type = type,
                owner_id = owner_id,
                item_id = item_id,
                sid = result['error']['captcha_sid'],
                key = captcha_key,
                ver = config.API_VERSION), headers=newheaders).json()
            #print(result)
            if 'error' in result.keys():
                #print(result)
                return result['error']['error_code']
            return result
        return result['error']['error_code']
    return result

@client.task
def process_friends(data):
    count_of_frinds = 0
    target, vk_token, from_user_id, chat_id = data['target'], data['vk_token'], data['from_user_id'], data['chat_id']
    #Получаем стену пользователя
    wall = get_wall(target, vk_token)
    time.sleep(0.2)
    try:
        if 'response' in wall.keys():
        #Обходим 20 последних постов со стены
            for item in wall['response']['items']:
                type = item['type']
                id = item['id']
            
                #Получаем пользователей, поставивших лайки к посту
                likes = get_likes(type, target, id, vk_token)
                time.sleep(0.2)
                if 'response' in likes.keys():
                    for liker_id in likes['response']['items']:
                        #Получаем данные пользователя, лайкнувшего пост
                        liker = get_users(liker_id, vk_token)
                        time.sleep(0.2)
                        if 'response' in liker.keys():
                            try:
                                bdate = liker['response'][0]['bdate']
                            except:
                                bdate = '1.1.1900'
                            if len(bdate) < 6:
                                bdate = bdate+'.1900'
                            #Добавляем потенциального друга в базу
                            me = User.get(user_id = from_user_id)
                            try:
                                friend, is_new = Friend.get_or_create(
                                    user_id = liker_id,
                                    first_name = liker['response'][0]['first_name'],
                                    last_name = liker['response'][0]['last_name'],
                                    sex = liker['response'][0]['sex'],
                                    owner = me,
                                    bdate = datetime.datetime.strptime(bdate, '%d.%m.%Y')
                                )
                            except:
                                pass
                            #Проверяем друзья ли мы
                            friend_status = are_we_friends(liker_id, vk_token)
                            print('Status: ' + str(friend_status['response'][0]['friend_status']))
                            time.sleep(0.2)
                            if 'response' in friend_status:
                                #Если нет, то отправляем заявку в друзья
                                if int(friend_status['response'][0]['friend_status']) == 0 and int(liker['response'][0]['sex']) == 1:                                
                                    add = add_friend(liker_id, vk_token)
                                    print('Add friend: ' + liker['response'][0]['first_name'] + ' ' + str(add))
                                    time.sleep(0.2)
                                    if add in [1, 2, 4]:
                                        count_of_frinds += 1
                                    if int(add) == 15:
                                        #Ошибка токена
                                        msg = 'Ошибка токена. Отправлено заявок в друзья: {count_of_friends}.'.format(
                                                    count_of_friends = count_of_frinds
                                                )
                                        send_msg(chat_id, msg)
                                        return 15 
                                    if int(add) == 9:
                                        #Достигнут лимит на день
                                        msg = 'На сегодня все. Отправлено заявок в друзья: {count_of_friends}.'.format(
                                                    count_of_friends = count_of_frinds
                                                )
                                        send_msg(chat_id, msg)
                                        return 9
    except:
        pass                            
    msg = 'На сегодня все. Отправлено заявок в друзья: {count_of_friends}.'.format(
                                                    count_of_friends = count_of_frinds
                                                )
    send_msg(chat_id, msg)
    return 200

def send_msg(chat_id, text):
    response = requests.post('https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}'.format(
        token = config.TELEGRAM_TOKEN,
        chat_id = chat_id,
        text = text
    ))
    
    
@client.task
def process_likes(data):
    vk_token, from_user_id, chat_id = data['vk_token'], data['from_user_id'], data['chat_id']
    
    count = 0
    total_likes = 0
    user = User.get(user_id = from_user_id)
    for user in Friend.select().join(User).where(User.user_id == from_user_id):
        print('Use: ' + user.first_name)
        count += 1
        wall = {}
        owner_id = user.user_id
        
        wall = get_wall(owner_id, vk_token)
        if wall == 5:
            #Ошибка токена
            msg = 'Ошибка токена. Отправлено заявок в друзья: {total_likes}.'.format(
                        total_likes = total_likes
                    )
            send_msg(chat_id, msg)
            return  
            
        time.sleep(0.5)
        try:            
            if 'response' in wall.keys():
                if wall != {}:
                    i = 0
                    try:
                        for item in wall['items']:
                            if i >= 2:
                                break
                            type = item['type']
                            item_id = item['id']
                            liked = is_liked(type, owner_id, item_id, vk_token)
                            time.sleep(0.5) 
                            if liked == 0:
                                result = add_like(type, owner_id, item_id, vk_token)
                                print('Result of add like: ' + result)
                                if result == 5:
                                    #Ошибка токена
                                    msg = 'Ошибка токена. Поставлено лайков: {total_likes}.'.format(
                                                total_likes = total_likes
                                            )
                                    send_msg(chat_id, msg)
                                    return 15 
                                if result == 9:
                                    #Ошибка токена
                                    msg = 'На сегодня все. Поставлено лайков: {total_likes}.'.format(
                                                total_likes = total_likes
                                            )
                                    send_msg(chat_id, msg)
                                    return 15 
                                if 'likes' in result.keys():
                                    print('Like to: ' + user.first_name)
                                    total_likes += 1
                                time.sleep(0.5) 
                            i = i + 1
                    except:
                        pass 
        except:
            pass
    msg = 'На сегодня все. Поставлено лайков: {total_likes}.'.format(
                                                total_likes = total_likes
                                            )
    send_msg(chat_id, msg)
    return 200 
