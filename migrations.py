from peewee import *
from playhouse.migrate import *
from models import User, Friend, db

#db = SqliteDatabase('vk.db')
#migrator = SqliteMigrator(db)
migrator = PostgresqlMigrator(db)

is_active = BooleanField(default=True)

with db.atomic():
    #db.create_tables([User, Friend])

    migrate(
        migrator.add_column('user', 'is_active', is_active))
