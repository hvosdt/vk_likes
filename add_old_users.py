import tqdm
from models import User, Friend



file_users = open('old_users.txt', 'r')
file_friends = open('old_friends.txt', 'r')

for item in file_users:
    print(item)
    user_id, target, token, app_id, app_secret = item.split('|')
    
    user, is_new = User.get_or_create(
        user_id = user_id,
        target = target,
        token = token,
        app_id = app_id,
        app_secret = app_secret,
        )


for item in file_friends:
    print(item)
    user = User.get(user_id = '246612799')
    try:
        user_id, first_name, last_name, sex, owner, bdate = item.split('|')
    except:
        pass
    try:
        friend, is_new = Friend.get_or_create(
            user_id = user_id,
            first_name = first_name,
            last_name = last_name,
            sex = sex,
            owner = user,
            bdate = bdate
            )
    except:
        pass