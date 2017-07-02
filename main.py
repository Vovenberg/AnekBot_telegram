import telebot
import config
import eventlet
import requests
import logging

bot = telebot.TeleBot(config.token)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    posts = get_data()
    send_messages(posts, message.chat.id)


def send_messages(posts, chat_id):
    for i, post in enumerate(posts['response']):
        if (i >= 1):
            text_ = post["text"].replace("<br>", "\n").__add__('\n\n------№{}---------'.format(i+1))
            bot.send_message(chat_id, text_)

def get_data():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(config.url)
        return feed.json()
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


if __name__ == '__main__':
     bot.polling(none_stop=True)