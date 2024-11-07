# import necessary packages
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_admin import Admin
from flask_admin.contrib.peewee import ModelView
import config
from models import User

from peewee import PostgresqlDatabase
from flask_peewee.db import Database
from flask_login import LoginManager
from flask_login import login_user, logout_user
from flask_login import login_required

import requests
import json
from uuid import uuid4
# initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager(app)
login_manager.init_app(app)


app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['DATABASE'] = {
    'name': config.DB_NAME,
    'engine': 'peewee.PostgresqlDatabase',
    'user': config.DB_USERNAME,
    'password': config.DB_PASSWORD,
    'host': 'localhost'
}

# initialize the SQLAlchemy database
db = Database(app)

# create the admin panel
admin = Admin(app)
admin.add_view(ModelView(User))

from flask_login import UserMixin

class AdminVK(UserMixin):
    def __init__(self, id_, username, password):
        self.id = id_
        self.username = username
        self.password = password

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    users = {
        '1': AdminVK(1, 'username', 'password'),
    }
    return users.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            
            user = AdminVK(1, username, password)
            login_user(user)
            return redirect(url_for('dashboard'))
        else: 
            flash('Invalid login!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# define a route for the home page
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html')

# define a route for the dashboard page
@app.route('/dashboard')
@login_required
def dashboard():    
    users = User.select()
    return render_template('dashboard.html', users=users)

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
    
    app.run()