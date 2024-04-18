from peewee import *
import config

db = PostgresqlDatabase(config.DB_NAME, user=config.DB_USERNAME, password=config.DB_PASSWORD, host='vk_postgres')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = TextField(unique=True)
    vk_id = TextField(default='123')
    target = TextField(default='test')
    token = TextField(default='test')
    app_id = TextField(default='test')
    app_secret = TextField(default='test')
    target_sex = IntegerField(default=3)
    is_active = BooleanField(default=True)
    do_friends = BooleanField(default=True)
    do_likes = BooleanField(default=True)

class Friend(BaseModel):
    user_id = TextField()
    owner = ForeignKeyField(User, backref='friends')
    first_name = TextField(default='Василиса')
    last_name = TextField(default='Пупкина')
    sex = IntegerField(default=1)
    bdate = DateTimeField(default='01.1.1900')
    
with db.atomic():
    #db.drop_tables([User])
    try:
        db.create_tables([User])
    except: pass
    #db.evolve(interactive=True)
    
    #migrate(
    #    migrator.add_column('user', 'order_type', order_type))    
