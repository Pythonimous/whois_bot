import telegram.error

from .config import chats, users, bot


def new_chat(chat_id, chat_name):
    chats.insert_one(
        {
            "_id": str(chat_id),
            "name": chat_name,
            "users": []
        }
    )


def new_user(user_id, username):
    if not users.find_one(filter={"_id": str(user_id)}):
        users.insert_one(
            {
                '_id': str(user_id),
                'username': username,
                'chats': {}
            }
        )


def new_username(user_id, username):
    users.update_one(
        filter={'_id': str(user_id)},
        update={
            '$set': {"username": username}
        }
    )


def new_chatname(chat_id, chat_name):
    chats.update_one(
        filter={'_id': str(chat_id)},
        update={
            '$set': {"name": chat_name},
        }
    )


def user_joins_chat(chat_id, user_id):
    users.update_one(
        filter={'_id': str(user_id)},
        update={
            '$set': {f"chats.{str(chat_id)}":
                     {'violations': 0,
                      'need_intro': 1,  # flag to distinguish new and  old members and force new to introduce
                      'info': {}
                      }
                     }
        }
    )
    chats.update_one(
        filter={'_id': str(chat_id)},
        update={
            '$push': {"users": str(user_id)}
        }
    )


def get_user(user_id):
    return users.find_one(
        filter={"_id": str(user_id)}
    )


def get_chat_user(chat_id, user_id):
    return users.find_one(filter={
        "_id": str(user_id),
        f"chats.{str(chat_id)}": {"$exists": True}
    })


def get_user_chats(user_id):
    return get_user(user_id)["chats"]


def get_user_language(user_id):
    return get_user(user_id).get("lang", "en")


def user_leaves_chat(chat_id, user_id):

    user = get_chat_user(chat_id, user_id)
    try:
        bot.deleteMessage(chat_id, user["chats"][str(chat_id)]["greeting_id"])
    except telegram.error.BadRequest:
        print('{}: {} - Message too old'.format(chat_id, user_id))

    users.update_one(
        filter={'_id': str(user_id)},
        update={
            '$unset': {f"chats.{str(chat_id)}": 1}
        }
    )

    chats.update_one(
        filter={'_id': str(chat_id)},
        update={
            '$pull': {"users": str(user_id)}
        }
    )

    if not users.find_one({"_id": str(user_id)})["chats"]:
        users.delete_one({"_id": str(user_id)})


def bot_leaves_chat(chat_id):
    chats.delete_one({'_id': str(chat_id)})
    users.update_many(filter={f"chats.{str(chat_id)}": {"$exists": True}},
                      update={'$unset': {f"chats.{str(chat_id)}": 1}})
    to_remove = []
    for user in users.find():
        if not user["chats"]:
            to_remove.append(user["_id"])
    for user_id in to_remove:
        users.delete_one({"_id": user_id})
