import config
import requests
import time, datetime
from models import User, Friend
import vk_captchasolver as vc
#from celery import Celery
from handlers import client

#client = Celery('vk_like', broker=config.CELERY_BROKER_URL)
#client.conf.result_backend = config.CELERY_RESULT_BACKEND

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
    target, vk_token, from_user_id = data['target'], data['vk_token'], data['from_user_id']
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
                                    if add == 15:
                                        #Ошибка токена
                                        return 15 
                                    if add == 9:
                                        #Достигнут лимит на день
                                        return 9
    except:
        pass                            
    return count_of_frinds