class Post:
    id = 0
    text = ""
    likes = 0

    def __init__(self, id, text, likes):
        self.id = id
        self.text = text
        self.likes = likes