import config
import time
import datetime
import requests
from celery import Celery
from celery.schedules import crontab

from models import User, Friend
from api_functions import get_VK_token, get_target, send_msg, get_wall, get_friends, get_users, get_likes, are_we_friends, add_friend, add_like, is_liked

client = Celery('vk_like', broker=config.CELERY_BROKER_URL)
client.conf.result_backend = config.CELERY_RESULT_BACKEND
client.conf.timezone = 'Europe/Moscow'


client.conf.beat_schedule = {
    'cron_friends': {
        'task': 'vk_celery.cron_friends',
        'schedule': crontab(hour=config.FRIENDS_HOUR, minute=config.FRIENDS_MINUTE)
    },
    'cron_likes': {
        'task': 'vk_celery.cron_likes',
        'schedule': crontab(hour=config.LIKES_HOUR, minute=config.LIKES_MINUTE)
    }
}

@client.task
def cron_friends():
    users = User.select().where(User.do_friends == True)
    for user in users:
        vk_token = get_VK_token(user.user_id)
        target = get_target(user.user_id)
        print(vk_token)
        
        data = {}
        data['target'] = target
        data['vk_token'] = vk_token
        data['from_user_id'] = user.user_id
        data['chat_id'] = user.user_id
        send_msg(user.user_id, 'Пошел искать друзей!')
        process_friends.apply_async(args=[data])

@client.task
def cron_likes():
    users = User.select().where(User.do_likes == True)
    for user in users:
        vk_token = get_VK_token(user.user_id)
        print(vk_token)
        
        data = {}
        
        data['vk_token'] = vk_token
        data['from_user_id'] = user.user_id
        data['chat_id'] = user.user_id
        send_msg(user.user_id, 'Пошел ставить лайки!')
        process_likes.apply_async(args=[data])
        
@client.task
def process_friends(data):
    count_of_frinds = 0
    target, vk_token, from_user_id, chat_id = data['target'], data['vk_token'], data['from_user_id'], data['chat_id']
    #Получаем стену пользователя
    wall = get_wall(target, vk_token)
    
    #Получаем моих друзей
    my_friends = get_friends(vk_token)
    
    time.sleep(0.2)
    if 'error' in wall.keys():
            #print(result)
            if wall['error']['error_code'] == 5:
                #Ошибка токена
                msg = 'Ошибка токена. Отправлено заявок: {count_of_frinds}.'.format(
                            count_of_frinds = count_of_frinds
                        )
                send_msg(chat_id, msg)
                return 5
            else:
                print('Error: '+ str(wall['error']['error_code']))
                pass

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
                            print('Добавлен в базу: ' + friend.first_name)
                        except:
                            pass
                        
                        liker_sex = int(liker['response'][0]['sex'])
                        #print('Likersex : ' + str(liker_sex))
                        target_sex = me.target_sex
                        if target_sex == 3:
                            list_sex = [0, 1, 2]
                        else:
                            list_sex = [0, int(target_sex)]
                            
                        #print('Sex of target: ' + str(target_sex))
                        #Проверяем друзья ли мы
                        friend_status = are_we_friends(liker_id, vk_token)
                        
                        #print('Status: ' + str(friend_status['response'][0]['friend_status']))
                        time.sleep(0.2)
                        if 'response' in friend_status:
                            #Если нет, то отправляем заявку в друзья
                            if int(friend_status['response'][0]['friend_status']) == 0 and liker_sex in list_sex:
                                add = add_friend(liker_id, vk_token)
                                #print('Add friend: ' + liker['response'][0]['first_name'] + ' ' + str(add))
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
                                    msg = 'На сегодня все. Достигнут дневной лимит. Отправлено заявок в друзья: {count_of_friends}.'.format(
                                                count_of_friends = count_of_frinds
                                            )
                                    send_msg(chat_id, msg)
                                    return 9
                            
    msg = 'На сегодня все. Похоже, что пора поставить новую цель. Отправлено заявок в друзья: {count_of_friends}.'.format(
                                                    count_of_friends = count_of_frinds
                                                )
    send_msg(chat_id, msg)
    return 200

@client.task
def process_likes(data):
    vk_token, from_user_id, chat_id = data['vk_token'], data['from_user_id'], data['chat_id']
    
    count = 0
    total_likes = 0
    
    friends = get_friends(vk_token)
    if 'error' in friends.keys():
        print(result)
        if friends['error']['error_code'] == 5:
            #Ошибка токена
            msg = 'Ошибка токена. Поставлено лайков: {total_likes}.'.format(
                        total_likes = total_likes
                    )
            send_msg(chat_id, msg)
            return 5
        else:
            print('Error: '+ str(wall['error']['error_code']))
            pass
                
        time.sleep(0.5)
           
    if 'response' in friends.keys():
        res = friends['response']
        #print(friends['response'])
        l_friends = res['count']
        list_of_friends = res['items']
        #user = User.get(user_id = from_user_id)
        #lf = len(Friend.select().join(User).where(User.user_id == from_user_id))
        send_msg(chat_id, 'У вас сейчас {l} друзей. Неплохо для начала'.format(
            l = l_friends
        ))
        for item in list_of_friends:
            #print('Use: ' + owner_id)
            count += 1
            wall = {}
            owner_id = item
            
            wall = get_wall(owner_id, vk_token)
            if 'error' in wall.keys():
                #print(result)
                if wall['error']['error_code'] == 5:
                    #Ошибка токена
                    msg = 'Ошибка токена. Поставлено лайков: {total_likes}.'.format(
                                total_likes = total_likes
                            )
                    send_msg(chat_id, msg)
                    return 5
                else:
                    print('Error: '+ str(wall['error']['error_code']))
                    pass
                    
            time.sleep(0.5)
            
            if 'response' in wall.keys():
                #print('Take wall' + owner_id)
                if wall != {}:
                    i = 0
                    
                    for item in wall['response']['items']:
                        #print('Items of: ' + user.first_name)
                        if i >= 2:
                            break
                        type = item['type']
                        item_id = item['id']
                        liked = is_liked(type, owner_id, item_id, vk_token)['response']
                        #print('Liked: ' + str(liked))
                        time.sleep(0.5) 
                        
                        if liked['liked'] == 0:
                            result = add_like(type, owner_id, item_id, vk_token)
                            #print('Result of add like: ' + str(result))
                            if result == 5:
                                #Ошибка токена
                                msg = 'Ошибка токена. Поставлено лайков: {total_likes}.'.format(
                                            total_likes = total_likes
                                        )
                                send_msg(chat_id, msg)
                                return 15 
                            if result == 9:
                                #Ошибка токена
                                msg = 'На сегодня все, достигнут лимит. Поставлено лайков: {total_likes}.'.format(
                                            total_likes = total_likes
                                        )
                                send_msg(chat_id, msg)
                                return 15 
                            try:
                                l = result['response']
                                if 'likes' in l.keys():
                                    #print('Like to: ' + user.first_name)
                                    total_likes += 1
                                time.sleep(0.5) 
                            except:
                                pass
                        i = i + 1
            

    msg = 'На сегодня все. проверил всех друзей. Поставлено лайков: {total_likes}.'.format(
                                                total_likes = total_likes
                                            )
    send_msg(chat_id, msg)
    return 200 
        
    
    

