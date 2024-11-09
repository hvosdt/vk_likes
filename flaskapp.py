# import necessary packages
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import config

import requests
import json
from uuid import uuid4
import base64
import re
import os
import hashlib
import pkce

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
        code = params['code']
        device_id = params['device_id']
        state = params['state']
        client_id = config.CLIENT_ID
        with open('state1.txt', 'w') as file:
            file.write(str(session[state]))
        data = {
            'code': code,
            'client_id': client_id,
            'redirect_uri': config.REDIRECT_URL,
            'device_id': device_id,
            'state': state,
            'grant_type': 'authorization_code',
            'code_verifier': session[state]
        }
        url = 'https://id.vk.com/oauth2/auth'
        res = requests.post(url, data=data).json()
        with open('vk_id.json', 'w') as file:
            json.dump(res, file, indent=4)
        
        result = {
            'status': 'Success'
        }
        response = make_response(jsonify(result), 200)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
@app.route('/vk_auth')
def vk_auth():
    code_verifier, code_challenge = pkce.generate_pkce_pair()
    state = uuid4()
    with open('state.txt', 'w') as file:
        file.write(str(code_verifier))
    session[str(state)] = code_verifier
    
    return render_template('vk_auth.html', APP_ID=config.CLIENT_ID, REDIRECT_URL=config.REDIRECT_URL, STATE=state, CODE_CHALLENGE=code_challenge)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8000)    