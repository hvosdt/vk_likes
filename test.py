from models import User, Friend, db
import tqdm

with open('old_friends.txt', 'w') as file:
    friends = []
    for user in Friend.select().order_by(Friend.id):
        user_id = user.user_id
        first_name = user.first_name
        last_name = user.last_name
        sex = user.sex
        owner = user.owner
        bdate = user.bdate
        item = '{user_id}|{first_name}|{last_name}|{sex}|{owner}|{bdate}'.format(
            user_id = user_id.strip(),
            first_name = first_name.strip(),
            last_name = last_name.strip(),
            sex = sex,
            owner = owner,
            bdate = bdate
        )
        friends.append(item)
        file.write(item + '\n')

with open('old_users.txt', 'w') as file:
    users = []
    for user in User.select().order_by(User.id): 
        user_id = user.user_id
        target = user.target
        token = user.token
        app_id = user.app_id
        app_secret = user.app_secret

        
        item = '{user_id}|{target}|{token}|{app_id}|{app_secret}'.format(
            user_id = user_id,
            target = target,
            token = token,
            app_id = app_id,
            app_secret = app_secret
        )
        print(item)
        users.append(item)
        file.write(item + '\n')