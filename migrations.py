from peewee import *
from playhouse.migrate import *
from models import User, Friend, db

#db = SqliteDatabase('vk.db')
#migrator = SqliteMigrator(db)
migrator = PostgresqlMigrator(db)

do_friends = BooleanField(default=True)
do_likes = BooleanField(default=True)

with db.atomic():
    #db.create_tables([User, Friend])

    migrate(
        migrator.add_column('user', 'do_friends', do_friends))
    migrate(
        migrator.add_column('user', 'do_likes', do_likes))

