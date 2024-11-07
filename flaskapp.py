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
    response = make_response(jsonify({'status': 'success'}), 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = ['GET', 'POST']
    return response       
        
@app.route('/vk_auth')
def vk_auth():    
    return render_template('vk_auth.html', APP_ID=config.CLIENT_ID, REDIRECT_URL=config.REDIRECT_URL, STATE=uuid4())

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)