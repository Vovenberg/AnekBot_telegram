import sqlite3


class DataBaseDao:
    def __init__(self):
        self.con = sqlite3.connect('dataBase.db')
        self.cursor = self.con.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS post (id INT PRIMARY KEY, text TEXT, likes INT)")

    def create_single(self, post):
        values__format = 'INSERT INTO post VALUES ({0},\'{1}\',{2})'.format(post.id, post.text, post.likes)
        return self.cursor.execute(
            values__format).fetchall()

    def select_single(self, id):
        return self.cursor.execute('SELECT * FROM post where id = {}'.format(id)).fetchall()

    def select_random_single(self):
        return self.cursor.execute('SELECT * FROM post ORDER BY RANDOM() LIMIT 1').fetchall()

    def select_all(self):
        return self.cursor.execute('SELECT * FROM post').fetchall()

    def selectId_all(self):
        return self.cursor.execute('SELECT id FROM post').fetchall()

    def select_few(self, ids):
        results = []
        for id in ids:
            results.extend(self.select_single(id))
        return results

    def create_few(self, posts):
        for post in posts:
            self.create_single(post)

    def post_not_exist(self, id):
        if (self.select_single(id) is None):
            return True
        else:
            return False

    def count_posts(self):
        return len(self.select_all())

    def close(self):
        self.con.close()
