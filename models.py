from peewee import *
import config

db = PostgresqlDatabase(config.DB_NAME, user=config.DB_USERNAME, password=config.DB_PASSWORD)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = TextField(unique=True)
    target = TextField(default='test')
    token = TextField(default='test')
    app_id = TextField(default='test')
    app_secret = TextField(default='test')
    target_sex = IntegerField(default=3)
    is_active = BooleanField(default=True)


class Friend(BaseModel):
    user_id = TextField()
    owner = ForeignKeyField(User, backref='friends')
    first_name = TextField(default='Василиса')
    last_name = TextField(default='Пупкина')
    sex = TextField(default='Женский')
    bdate = DateTimeField(default='01.1.1900')
    

     