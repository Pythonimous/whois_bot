from .base import new_chatname, new_username
from .config import chats, users
from .utils import get_username


def chatname_changes(function):
    def change_names(*args, **kwargs):
        """ Check for known chat name change """
        if not chats.count_documents(filter={'_id': args[0].message.chat.id, 'name': args[0].message.chat.title}):
            new_chatname(args[0].message.chat.id, args[0].message.chat.title)
        return function(*args, **kwargs)
    return change_names


def username_changes(function):
    def change_names(*args, **kwargs):
        """ Check for known user name changes """
        username = get_username(args[0])
        if users.count_documents(filter={'_id': args[0].message.from_user.id}):  # if we know the user
            if not users.count_documents({'_id': args[0].message.from_user.id, 'username': username}):  # under a different name
                new_username(args[0].message.from_user.id, username)
        return function(*args, **kwargs)
    return change_names
