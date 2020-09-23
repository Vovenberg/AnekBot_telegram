import logging
import random
import time
import eventlet
import requests
import telebot
import constants
from telebot import types
from telebot.util import async
from dao.topPostsDao import TopPostsDao
from dao.usersDao import UserDao
from dto.post import Post
from dto.user import CustomUser

bot = telebot.TeleBot(constants.token)
logging.basicConfig(level=logging.INFO)


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button_random = types.KeyboardButton(text="🤣Случайный анекдот")
    button_top10 = types.KeyboardButton(text="🏆ТОП10")
    button_last10 = types.KeyboardButton(text="☝️Последнее лучшее")
    keyboard.add(button_last10, button_top10)
    keyboard.add(button_random)
    UserDao().save_user(CustomUser(message.from_user, message.chat.id))
    bot.send_message(message.chat.id, 'Добро пожаловать, любитель хорошего юмора. Присаживайся поудобнее, начинаем...',
                     reply_markup=keyboard)


@bot.message_handler(commands=["info"])
def info(message):
    bot.send_message(message.chat.id,
                     '''Агрегатор анекдотов с группы ВК: https://vk.com/baneks
                     С вопросами и предложениями писать на email: v.kildushev@yandex.ru''')


@bot.message_handler(commands=["disable"])
def disableNotifications(message):
    UserDao().disable_notifications(message.from_user.id)
    logging.info(f'Notifications from user: {message.from_user} disabled')
    bot.send_message(message.chat.id, 'Уведомления отключены.')


@bot.message_handler(commands=["enable"])
def enableNotifications(message):
    UserDao().enable_notifications(message.from_user.id)
    logging.info(f'Notifications from user: {message.from_user} enabled')
    bot.send_message(message.chat.id, 'Уведомления включены.')


@bot.message_handler(commands=["stats"])
def stats(message):
    if (message.from_user.username == 'v_kildyushev'):
        for user in UserDao().get_all():
            bot.send_message(message.chat.id, f'Id: {user[2]}\n Username: {user[1]}\n'
                                              f'FirstName: {user[3]}\n SecondName: {user[4]}\n'
                                              f'Notifications: {user[5]}\n Clicks: {user[6]}')


@bot.message_handler(content_types=["text"])
def income_messages(message):
    UserDao().increment_clicks(message.from_user.username)
    chat_id = message.chat.id
    if message.text == '☝️Последнее лучшее':
        get_last_posts(chat_id, 5)
    if message.text == '🏆ТОП10':
        get_top(chat_id)
    if message.text == '🤣Случайный анекдот':
        get_random(chat_id)


def get_top(chat_id):
    dao = TopPostsDao()
    top10 = dao.select_all()[0: 10]
    dao.close()
    send_messages(top10, chat_id)


def get_last_posts(chat_id, count):
    umoreski = get_data_from_umoreski(30)
    posts = get_data(30)
    posts.extend(umoreski)
    posts.sort(key=lambda post: post.likes)
    posts.reverse()
    top: list = posts[0:20]
    results = []
    while count > 0:
        rand = random.randint(0, len(top) - 1)
        results.append(top[rand])
        top.remove(top[rand])
        count -= 1
    send_messages(results, chat_id)


def get_random(chat_id):
    dao = TopPostsDao()
    post = dao.select_random_single()
    dao.close()
    send_messages(post, chat_id)


#########################################

def send_messages(posts, chat_id):
    if (isinstance(posts, list) and len(posts) > 1):
        text_array = []
        m = 2 if (len(posts) % 2 != 0) else 1 if (len(posts) == 2) else 3
        for i, post in enumerate(posts):
            text = ''
            if (len(posts) > 1):
                text = f'\n\n------№{i + 1}---------\n'
            full_text = text.__add__(post.text.replace("<br>", "\n")) \
                .__add__(f'\n\nРейтинг лайков: {post.likes}')
            text_array.append(full_text)
            if (i % m == 0):
                join = ''.join(text_array)
                bot.send_message(chat_id, join)
                text_array.clear()
    else:
        if (isinstance(posts, list)):
            posts = posts[0]
        text = posts.text.replace("<br>", "\n").__add__(
            f'\n\nРейтинг лайков: {posts.likes}')
        bot.send_message(chat_id, text)


def get_data_from_umoreski(count=10, offset=0):
    return get_data(count, offset, constants.urlUmoreski)


def get_data(count=10, offset=0, url=constants.urlCategoryB):
    timeout = eventlet.Timeout(10)
    try:
        feed_url = url.format(count, offset)
        feed = requests.get(feed_url).json()
        logging.info(f"Got feed by url='{feed_url}': {feed}")
        list = []
        if 'error' in feed: 
            return list
        for i, post in enumerate(feed['response']['items']):
            if (i >= 1 and len(post["text"]) > 50):
                list.append(Post(post["id"], post["text"], post["likes"]["count"]))
        len1 = len(list)
        if (len1 < count):
            list.extend(get_data(count - len1, offset + count))
        logging.info(f'Got data from VK. count={count},offset={offset}')
        return list
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def check_new_posts_vk():
    try:
        file = open(constants.FILENAME_LASTID, 'rt')
    except FileNotFoundError:
        file = open(constants.FILENAME_LASTID, 'wt')
        # s = str(get_data(1)[0].id)
        file.write(s)
        file.close()
        return
    last_id = file.read()
    if last_id is None or last_id == "":
        logging.error('Empty file with last id. Last id = 0.')
        last_id = 0
    logging.info(f'Last ID from file = {last_id}')

    lastPosts = get_data(20)
    if lastPosts is not None:
        maxId = last_id
        new_posts = []
        for post in lastPosts:
            if (post.id > int(last_id) and post.likes > 300):
                new_posts.append(post)
                if (post.id > int(maxId)):
                    maxId = post.id
        if (maxId != last_id):
            ids = UserDao().get_all_chatId_with_enabled_notifications()
            for id in ids:
                send_messages(new_posts, id[0])
            with open(constants.FILENAME_LASTID, 'wt') as file:
                file.write(str(maxId))
                file.close()
                logging.info(f'New last id wrote in file: {maxId}')
        else:
            logging.info('No new posts')
    logging.info('Finished scan new post')


#####################################################################

@async()
def ping_vk():
    # while True:
    #     check_new_posts_vk()
    #     time.sleep(60 * 10)


@async()
def ping_heroku():
    while True:
        requests.get(constants.urlApp)
        time.sleep(60 * 5)


def initDB():
    UserDao()
    top_dao = TopPostsDao()
    if (top_dao.count_posts() == 0):
        posts = get_data(100)
        posts.sort(key=lambda post: post.likes)
        posts.reverse()
        top_dao.create_few(posts[0:50])
        top_dao.close()


if __name__ == '__main__':
    initDB()
    # ping_vk()
    ping_heroku()
    bot.polling(none_stop=True)