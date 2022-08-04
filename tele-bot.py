import vk_api
import random
import telebot
import json
from telebot import types
from tokens import user_token, tgbot_token, bot_id

bot = telebot.TeleBot(tgbot_token)

vk_session = vk_api.VkApi(token=user_token)
vk = vk_session.get_api()
owner_id=bot_id
album_id=285527452
photos_dict = vk.photos.get(owner_id=owner_id, album_id=album_id)
photos_dict = vk.photos.get(owner_id=owner_id, album_id=album_id, count=photos_dict.get('count'))
photos_list = photos_dict.get('items')
photos = [photos_list[j]['sizes'][-1]['url'] for j in range(0, photos_dict.get('count')-1)]

with open('kuli4.json', 'r') as kuli4Json:
        kuli4_phrases = json.load(kuli4Json)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Привет!')

@bot.message_handler(content_types=["text"])
def witless_kuli4(message):
    try:
        bot.send_message(message.chat.id, random.choice(kuli4_phrases))
    except Exception as e:
        print(e)

@bot.inline_handler(lambda query: query.query == '')
def query_photo(inline_query):
    pics = random.sample(photos, k=50)
    try:
        res=[types.InlineQueryResultPhoto(id=i, photo_url=pics[i], thumb_url=pics[i]) for i in range(0, 50)]
        bot.answer_inline_query(inline_query.id, res)
    except Exception as e:
        print(e)
bot.polling()