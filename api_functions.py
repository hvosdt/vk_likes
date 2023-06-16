import config
import requests
from models import User

import vk_captchasolver as vc

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
            return ('-' + str(result['response'][0]['id']))
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
        '{api_uri}users.get?user_ids={user_ids}&v={ver}&fields=sex,bdate,first_name_acc'.format(
        api_uri = config.API_URL, 
        user_ids= user_ids,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result

def get_group(target, token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}groups.getById?group_id={q}&v={ver}'.format(
        api_uri = config.API_URL, 
        q = target,
        ver = config.API_VERSION), headers=newheaders).json()
    if 'error' in result.keys():
            print(result)
            return result['error']['error_code']
    return result


def get_friends(token):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}friends.get?v={ver}'.format(
        api_uri = config.API_URL,
        ver = config.API_VERSION), headers=newheaders).json()
    return result


def add_friend(user_id, token, hello_text):
    newheaders = {
    'Authorization': 'Bearer '+ token
    }
    result = requests.get(
        '{api_uri}friends.add?user_id={user_id}&text={text}&v={ver}'.format(
        api_uri = config.API_URL, 
        user_id= user_id,
        text = hello_text,
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
            #print(result)
            #captcha_key = vc.solve(sid=int(result['error']['captcha_sid']))
            print(result['error']['captcha_img'])
            #print(captcha_key)
            URL = result['error']['captcha_img']
            response = requests.get(URL)
            filename = str(result['error']['captcha_sid']) + '.png'
            open(filename, "wb").write(response.content)
            try:
                captcha_key = vc.solve(image=filename)
                print(captcha_key)
            except:
                captcha_key ='qwer'
            result = requests.get(
                '{api_uri}likes.add?type={type}&owner_id={owner_id}&item_id={item_id}&captcha_sid={sid}&captcha_key={key}&v={ver}'.format(
                api_uri = config.API_URL, 
                type = type,
                owner_id = owner_id,
                item_id = item_id,
                sid = result['error']['captcha_sid'],
                key = captcha_key,
                ver = config.API_VERSION), headers=newheaders).json()
        
            if 'error' in result.keys():
                #print(result)
                return result['error']['error_code']
            return result
        return result['error']['error_code']
    return result

def send_msg(chat_id, text):
    response = requests.post('https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}'.format(
        token = config.TELEGRAM_TOKEN,
        chat_id = chat_id,
        text = text
    ))