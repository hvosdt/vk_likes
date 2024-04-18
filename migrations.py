from peewee import *
from playhouse.migrate import *
from models import User, Friend, db

#db = SqliteDatabase('vk.db')
#migrator = SqliteMigrator(db)
migrator = PostgresqlMigrator(db)

#do_friends = BooleanField(default=True)
#do_likes = BooleanField(default=True)

vk_id = TextField(default='123')

with db.atomic():
    #db.create_tables([Friend])
    #db.drop_tables(Friend)

    migrate(
        migrator.add_column('user', 'vk_id', vk_id))
    

