from telegram import User
class User:
    id = 0
    username = ""
    chat_id = 0
    first_name = ""
    last_name = ""
    notifications = True
    count_clicks = 0

    def __init__(self, id, username, first_name, last_name, chat_id = 0, notifications = True, count_clicks = 0):
        self.id = id
        self.username = username
        self.chat_id = chat_id
        self.first_name = first_name
        self.last_name = last_name
        self.notifications = notifications
        self.count_clicks = count_clicks

    def __init__(self, user:User, chat_id):
        self.id = user.id
        self.username = user.username
        self.chat_id = chat_id
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.notifications = True
        self.count_clicks = 0
