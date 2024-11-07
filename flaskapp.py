# import necessary packages
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import config

import requests
import json
from uuid import uuid4

# initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# define a route for the home page
@app.route('/')
def index():
    response = make_response(jsonify({'status': 'success'}), 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = ['GET', 'POST']
    return response 
    

@app.route('/do_auth', methods=['POST', 'GET'])
def do_auth():
    if request.method == 'POST':
        data = request.json()
        with open('vk_code.json', 'w') as file:
            json.dump(data, file, indent=4)
        response = make_response(jsonify({'status': 'success'}), 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = ['GET', 'POST']
        return response 
        
@app.route('/callback', methods=['GET'])
def callback():
    if request.method == 'GET':
        params = request.args.to_dict()
        print(params)
        with open('vk_code.txt', 'w') as file:
            file.write(str(params))        
        payload = json.loads(params['payload'])
        silent_token = payload['token']
        uuid = payload['uuid']
        service_token = config.SERVICE_TOKEN
        data = {
            'token': silent_token,
            'access_token': service_token,
            'uuid': uuid,
            'v': '5.131'
        }
        url = 'https://api.vk.com/method/auth.exchangeSilentAuthToken'
        res = requests.post(url, data=data).json()
        with open('vk_id.json', 'w') as file:
            json.dump(res, file, indent=4)
        result = {
            'status': 'Success'
        }
        return make_response(jsonify(result), 200)    
        
@app.route('/vk_auth')
def vk_auth():    
    return render_template('vk_auth.html', APP_ID=config.CLIENT_ID, REDIRECT_URL=config.REDIRECT_URL, STATE=uuid4())

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)