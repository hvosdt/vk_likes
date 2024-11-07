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
    return render_template('index.html')

@app.route('/callback', methods=['GET'])
def callback():
    group_id = 221262044
    if request.method == 'GET':
        params = request.args.to_dict()
        
        #with open('vk_code.txt', 'w') as file:
        #    file.write(str(params))
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
    return render_template('auth.html', APP_ID=config.CLIENT_ID, REDIRECT_URL=config.REDIRECT_URL, STATE=uuid4())

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)