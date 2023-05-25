from peewee import *
from playhouse.migrate import *
from models import User, Friend, db

#db = SqliteDatabase('vk.db')
#migrator = SqliteMigrator(db)
migrator = PostgresqlMigrator(db)

token = IntegerField(default=3)

with db.atomic():
    #db.create_tables([User, Friend])

    migrate(
        migrator.add_column('user', 'target_sex', token))
