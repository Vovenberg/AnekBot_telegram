import sqlite3


class UserDao:
    def __init__(self):
        self.con = sqlite3.connect('users.db')
        self.cursor = self.con.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user (id INT PRIMARY KEY, username TEXT, chat_id INT, first_name TEXT, last_name TEXT, notifications BOOLEAN DEFAULT TRUE, count_clicks INT DEFAULT 0)")

    def save_user(self, user):
        query = f"INSERT INTO user(id,username,chat_id,first_name,last_name) VALUES ({user.id},'{user.username}',{user.chat_id},'{user.first_name}','{user.last_name}')"
        self.cursor.execute(query)
        self.con.commit()
        return self.con

    def get_by_id(self, id):
        return self.cursor.execute(f'SELECT * FROM user where id = {id}').fetchall()

    def get_by_username(self, username):
        return self.cursor.execute(f"SELECT * FROM user where username = '{username}'").fetchall()

    def get_all(self):
        return self.cursor.execute(f'SELECT * FROM user').fetchall()

    def enable_notifications(self, username):
        self.cursor.execute(f"UPDATE user SET notifications = 1 where username = '{username}'").fetchall()
        self.con.commit()
        self.con.close()

    def disable_notifications(self, username):
        self.cursor.execute(f"UPDATE user SET notifications = 0 where username = '{username}'").fetchall()
        self.con.commit()
        self.con.close()

    def get_all_chatId_with_enabled_notifications(self):
        return self.cursor.execute(f'SELECT chat_id FROM user WHERE notifications = 1 ').fetchall()

    def increment_clicks(self, username):
        self.cursor.execute(f"UPDATE user SET count_clicks = count_clicks + 1 where username = '{username}'").fetchall()
        self.con.commit()
        self.con.close()

    def close(self):
        self.con.close()
