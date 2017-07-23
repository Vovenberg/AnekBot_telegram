import telebot
import config
import eventlet
import requests
import logging
import time
from telebot.util import async
from telebot import types
from post import Post
from topPostsDao import DataBaseDao

bot = telebot.TeleBot(config.token)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    buttons = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    buttons.add("Последние 10")
    buttons.add("ТОП10")
    buttons.add("Случайный анекдот")
    bot.register_next_step_handler(message, process_step)


def process_step(message):
    chat_id = message.chat.id
    if message.text == 'Последние 10':
        get_last_posts(chat_id, 10)
    if message.text == 'ТОП10':
        get_top(chat_id)
    if message.text == 'Случайный анекдот':
        get_random(chat_id)


def get_top(chat_id):
    dao = DataBaseDao()
    top10 = dao.select_all()[0 : 10]
    dao.close()
    send_messages(top10, chat_id)


def get_last_posts(chat_id, count):
    posts = get_data(count)
    posts.sort(key=sortByLikes)
    send_messages(posts, chat_id)

def get_random(chat_id):
    dao = DataBaseDao()
    post = dao.select_random_single()
    dao.close()
    send_messages(post, chat_id)


#########################################
def send_messages(posts, chat_id):
    if (isinstance(posts, list)):
        text_array = []
        for i, post in enumerate(posts):
            text = ''
            if (len(posts) > 1):
                text = f'\n\n------№{i + 1}---------\n'
            full_text = text.__add__(post.text.replace("<br>", "\n")) \
                .__add__(f'\n\nРейтинг лайков: {post.likes}')
            text_array.append(full_text)
            if (i % 3 == 0):
                join = ''.join(text_array)
                bot.send_message(chat_id, join)
                text_array.clear()
    else:
        text = posts.text.replace("<br>", "\n").__add__(
            f'\n\nРейтинг лайков: {posts.likes}')
        bot.send_message(chat_id, text)


def get_data(count = 10, offset = 0):
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(config.url.format(count, offset))
        list = []
        for i, post in enumerate(feed.json()['response']):
            if (i >= 1 and len(post["text"]) > 50):
                list.append(Post(post["id"], post["text"], post["likes"]["count"]))
        len1 = len(list)
        if (len1 < count):
            list.extend(get_data(count-len1, offset + count))
        logging.info(f'Got data from VK. count={count},offset={offset}')
        return list
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()

def sortByLikes(post: Post):
    return post.likes


def check_new_posts_vk():
    try:
        file = open(config.FILENAME_LASTID, 'rt')
    except FileNotFoundError:
        file = open(config.FILENAME_LASTID, 'wt')
        s = str(get_data(1)[0].id)
        file.write(s)
        file.close()
        return
    last_id = file.read()
    if last_id is None or last_id == "":
        logging.error('Empty file with last id. Last id = 0.')
        last_id = 0
    logging.info(f'Last ID from file = {last_id}')

    lastPosts = get_data(10)
    if lastPosts is not None:
        maxId = last_id
        new_posts = []
        for post in lastPosts:
            if (post.id > int(last_id)):
                new_posts.append(post)
                if (post.id > int(maxId)):
                    maxId = post.id
        if (maxId != last_id):
            send_messages(new_posts, config.CHAT_ID)
            with open(config.FILENAME_LASTID, 'wt') as file:
                file.write(str(maxId))
                file.close()
                logging.info(f'New last id wrote in file: {maxId}')
        else:
            logging.info('No new posts')
    logging.info('Finished scan new post')


@async()
def ping_vk():
    while True:
        check_new_posts_vk()
        time.sleep(60 * 10)


def initDB():
    dao = DataBaseDao()
    if (dao.count_posts() == 0):
        posts = get_data(1000)
        posts.sort(key=sortByLikes)
        posts.reverse()
        dao.create_few(posts[0:500])
        dao.close()

if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO,
                        filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    initDB()
    ping_vk()
    bot.polling(none_stop=True)
