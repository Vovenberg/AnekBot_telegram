import sqlite3

from dto.post import Post


class TopPostsDao:
    def __init__(self):
        self.con = sqlite3.connect('topPosts.db')
        self.cursor = self.con.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS post (id INT PRIMARY KEY, text TEXT, likes INT)")

    def create_single(self, post):
        try:
            query = f"INSERT INTO post(id,text,likes) VALUES ({post.id},'{post.text}',{post.likes})"
            executed = self.cursor.execute(query)
            self.con.commit()
            return executed.fetchall()
        except sqlite3.OperationalError as e:
            pass

    def select_single(self, id):
        return convertToPostArray(self.cursor.execute(f'SELECT * FROM post where id = {id}').fetchall())

    def select_random_single(self):
        return convertToPostArray(self.cursor.execute('SELECT * FROM post ORDER BY RANDOM() LIMIT 1').fetchall())

    def select_all(self):
        return convertToPostArray(self.cursor.execute('SELECT * FROM post').fetchall())

    def selectId_all(self):
        return convertToPostArray(self.cursor.execute('SELECT id FROM post').fetchall())

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


def convertToPostArray(resultArray):
    listPosts = []
    for result in resultArray:
        listPosts.append(Post(result[0], result[1], result[2]))
    return listPosts
