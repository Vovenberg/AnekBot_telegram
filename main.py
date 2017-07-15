import telebot
import config
import eventlet
import requests
import logging
import random
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
    bot.send_message(chat_id=message.chat.id, text="Анекдот в студию!", reply_markup=buttons)
    bot.register_next_step_handler(message, process_step)


def process_step(message):
    chat_id = message.chat.id
    if message.text == 'Последние 10':
        get_last_10(chat_id)
    if message.text == 'ТОП10':
        get_top(chat_id)
    if message.text == 'Случайный анекдот':
        get_random(chat_id)


def get_top(chat_id):
    posts = get_top_posts()
    send_messages(posts, chat_id)


def get_last_10(chat_id):
    posts = get_data(config.url)
    send_messages(posts, chat_id)


def get_random(chat_id):
    dao = DataBaseDao()
    post = dao.select_random_single()
    if (len(post)==0):
        post = get_data(config.urlLast100)[random.randint(0, 99)]
    send_messages(post, chat_id)
    dao.close()


#########################################
def send_messages(posts, chat_id):
    if (isinstance(posts, list)):
        text_array = []
        for i, post in enumerate(posts):
            text = '\n\n------№{}---------\n'.format(i + 1).__add__(post.text.replace("<br>", "\n")).__add__(
                '\n\nРейтинг лайков: {}'.format(post.likes))
            text_array.append(text)
            if (i % 3 == 0):
                join = ''.join(text_array)
                bot.send_message(chat_id, join)
                text_array.clear()
    else:
        text = posts.text.replace("<br>", "\n").__add__(
            '\n\nРейтинг лайков: {}'.format(posts.likes))
        bot.send_message(chat_id, text)


def get_data(url):
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(url)
        list = []
        for i, post in enumerate(feed.json()['response']):
            if (i >= 1 and len(post["text"]) > 50):
                list.append(Post(post["id"], post["text"], post["likes"]["count"]))
        return list
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def get_top_posts():
    dao = DataBaseDao()
    if (dao.count_posts() == 0):
        offset = 0
        posts = []
        while offset < 1000:
            data = get_data(config.urlTop.format(offset))
            posts.extend(data)
            offset += 100
        posts.sort(key=sortByLikes)
        top100 = posts[0:100]
        dao.create_few(top100)
        dao.close()
        return top100
    else:
        top100 = dao.select_all()
        dao.close()
        return top100


def sortByLikes(post:Post):
    return post.likes


if __name__ == '__main__':
    bot.polling(none_stop=True)
