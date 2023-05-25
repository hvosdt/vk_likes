import requests
import config
from flask import Flask,request
from furl import furl
from models import User
from urllib.parse import urlparse

app = Flask(__name__)
#client_id = '51651572'
#client_secret = '2SrqvD43OOk0LHnBgJ9A'
redirect_url = '{url}/vkcreds'.format(url = config.REDIRECT_URL)


#url = 'https://oauth.vk.com/authorize?client_id=51651572&display=page&redirect_uri=http://localhost/vkcreds/51651572&scope=offline,wall,photos,groups,docs,friends,stories,notifications&response_type=code&v=5.131'

@app.route('/')
def hello():
    return 'Webhooks with Python'

@app.route('/vkcreds/<id>',methods=['GET', 'POST'])    
def vkcreds(id):
    result = furl(request)
    print(result.args)
    print(request.base_url)
    '''
    scheme = urlparse(request)
    print(scheme.fragment)
    query = User.get(app_id = id)
    app_secret = query.app_secret
    result = furl(request)
    print(result)
    
    code = result.args['access_token']
    
    token_url = 'https://oauth.vk.com/access_token?client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_url}/{client_id}&code={code}'.format(
        client_id = id,
        client_secret = app_secret,
        redirect_url = redirect_url,
        code = code
    )
    
    result = requests.get(token_url).json()
    print('this is token!')
    print(result['access_token'])
    data = {'token': result['access_token']}
    #query = User.update(data).where(User.app_id==id)
    query = User.update(data).where(User.app_id==id)
    query.execute()
    #query.token = result['access_token']
    print('Новый токен')
    query = User.get(app_id = id)
    print(query.token)
    '''
    return 'OK'
    
        #file = open('auth_key.txt', 'w')
        #file.write(request)
        #file.close(
        
if __name__ == '__main__':
    app.run(port=80, debug=True)
