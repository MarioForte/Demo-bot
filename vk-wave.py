import asyncio
import json
import random
from collections import defaultdict
import vk_api

from vkwave.bots import SimpleLongPollBot, SimpleBotEvent
from vkwave.bots.core.dispatching import filters
from vkwave.api import API
from vkwave.bots.utils.uploaders import PhotoUploader
from vkwave.client import AIOHTTPClient

from tokens import user_token, bot_token, bot_id, audio_dict, gif, mos_vid, admin_list, kuli4_audio, banned_nicks
from db import BotDB
# Функция генерации актуального состава фотоальбома
def photos_list(owner_id, album_id):
    vk_session = vk_api.VkApi(
        token=user_token)
    vk = vk_session.get_api()
    photos_dict = vk.photos.get(owner_id=owner_id, album_id=album_id)
    photos_dict = vk.photos.get(
        owner_id=owner_id, album_id=album_id, count=photos_dict.get('count'))
    photos_list = photos_dict.get('items')
    return [f'photo{str(bot_id)}_{photos_list[j].get("id")}' for j in range(0, photos_dict.get('count'))]

# Присваивание переменным результаты прошлой функции дабы не вызывать ее каждый раз
def updater():
    global kuli4_list
    global cats_list
    global mosi4_list
    global vitalik_list
    global kuli4_phrases
    kuli4_list = photos_list(owner_id=bot_id, album_id=285527455) + kuli4_audio
    cats_list = photos_list(owner_id=bot_id, album_id=285527425)
    vitalik_list = list(audio_dict.values())
    mosi4_list = photos_list(owner_id=bot_id, album_id=285527452) + mos_vid
    with open('kuli4.json', 'r') as kuli4Json:
        kuli4_phrases = json.load(kuli4Json)
updater()
print('Bot ready')

# создание переменных
counter = defaultdict(int)
q_count = defaultdict(int)
q_from_id = defaultdict(int)
muted = {}


bot = SimpleLongPollBot(tokens=bot_token, group_id=-bot_id)
api = API(clients=AIOHTTPClient(), tokens=bot_token)
vk = api.get_context()
uploader = PhotoUploader(vk)
BotDB = BotDB('bot.db')


@bot.message_handler(filters.FromIdFilter(muted.keys()))
async def mute(event: SimpleBotEvent):
    await vk.messages.delete(delete_for_all=1, conversation_message_ids=event.object.object.message.conversation_message_id, peer_id=event.peer_id)


@bot.message_handler(filters.CommandsFilter("бот"))
async def botSend(event: SimpleBotEvent):
    try:
        attachment = await uploader.get_attachments_from_links(
        peer_id=event.peer_id,
        links=[i.url for i in event.attachments])
        await vk.messages.delete(delete_for_all=1, conversation_message_ids=event.object.object.message.conversation_message_id, peer_id=event.peer_id)
    finally:
        return await event.answer(message = " ".join(event.text.split()[1:]), attachment=attachment)


@bot.message_handler(filters.TextContainsFilter("кулич"))
async def kuli4(event: SimpleBotEvent):
    counter[event.peer_id] = 0
    if 'гс' in event.text.lower():
                await event.answer(attachment=random.choice(kuli4_audio))
                return
    elif random.randrange(1, 5) == 1:
        await event.answer(attachment=random.choice(kuli4_list))
    else:
        res = random.choice(kuli4_phrases)
        if res == '':
            return
        return res


@bot.message_handler(filters.TextContainsFilter(["кошка", "кот", "кис"]))
async def cats(event: SimpleBotEvent):
    text = event.text
    if not len(text.split(' ')) == 1 and text.split(' ')[1] != '1':
        if text.split(' ')[1].endswith('1') and not text.split(' ')[1].endswith(('11')):
            mad_suff = 'а'
        elif text.split(' ')[1].endswith(('2', '3', '4')) and not text.split(' ')[1].endswith(('12', '13', '14')):
            mad_suff = 'ов'
        else:
            mad_suff = 'ов'
        try:
            int(text.split(' ')[1])
        except ValueError:
            await event.answer(attachment=random.choice(cats_list))
            return
        if int(text.split(' ')[1]) <= 10 and text.split(' ')[1] != '0':
            await event.answer(attachment=random.sample(cats_list, int(text.split(' ')[1])))
        else:
            await event.reply(attachment=random.choice(cats_list), message=f'Как я тебе отправлю {text.split(" ")[1]} кот{mad_suff}? Держи одного.')
    else:
        await event.answer(attachment=random.choice(cats_list))


@bot.message_handler(filters.TextFilter('мут лист'))
async def mute_list(event: SimpleBotEvent):
    result = ''
    i = 0
    for id, time in muted.items():
        i += 1
        if BotDB.user_exists(id, event.peer_id):
            name = BotDB.get_name(id, event.peer_id)
        else:
            name = f'{(await vk.users.get(user_ids=id)).response[0].first_name} {(await vk.users.get(user_ids=id)).response[0].last_name}'
        result += f'{i}: {name}: {time} минут\n'
    if result == '':
        return 'Нет пользователей в муте.'
    result += '\nДля размута напишите Размут и номер в списке.'
    return result


@bot.message_handler(filters.TextStartswithFilter('мут'))
async def muter(event: SimpleBotEvent):
    chat = (await vk.messages.get_conversation_members(peer_id=event.peer_id)).response.items   
    admins = [i.member_id for i in chat if i.is_admin == True] + admin_list
    if event.from_id not in admins:
        return 'Вы не админ.'
    try:
        reply_id = event.object.object.message.reply_message.from_id
    except:
        return 'Кого нужно замутить?'
    if reply_id in admins:
        return 'Вы не можете замутить админа.'
    try:
        minutes = int(event.text.split(' ')[1])
    except ValueError:
        return 'Укажите время.'
    if reply_id in muted.keys():
        return 'Пользователь уже в муте.'
    muted[reply_id] = minutes
    if BotDB.user_exists(reply_id, event.peer_id):
        name = BotDB.get_name(reply_id, event.peer_id)
    else:
        name = (await vk.users.get(user_ids=reply_id)).response[0].first_name
    await event.answer(f'{name} получил мут на {minutes} минут.')
    await asyncio.sleep(minutes*60)
    try:
        del muted[reply_id]
        await event.answer(f'{name} размучен.')
    except KeyError:
        await event.answer(f'Похоже, что {name} был уже размучен.')


@bot.message_handler(filters.TextStartswithFilter('размут'))
async def unmute(event: SimpleBotEvent):
    chat = (await vk.messages.get_conversation_members(peer_id=event.peer_id)).response.items   
    admins = [i.member_id for i in chat if i.is_admin == True] + admin_list
    if event.from_id not in admins:
        return 'Вы не админ.'
    try:
        i = int(event.text.split(' ')[1])-1
    except ValueError:
        return 'Не указан пользователь, которого нужно размутить'
    try:
        id = list(muted.keys())[i]
    except IndexError:
        return 'Такого пользователя нет в списке'
    if BotDB.user_exists(id, event.peer_id):
        name = BotDB.get_name(id, event.peer_id)
    else:
        name = (await vk.users.get(user_ids=id)).response[0].first_name
    await event.answer(f'{name} был размучен')
    del muted[id]


@bot.message_handler(filters.TextFilter('ники'))
async def nicks(event: SimpleBotEvent):
    result = ''
    for user_id, name in BotDB.get_users_nicks(event.peer_id):
        result += f'{name}: [id{user_id}|{(await vk.users.get(user_ids=user_id)).response[0].first_name} {((await vk.users.get(user_ids=user_id)).response[0].last_name)[0]}.]\n'
    if result == '':
        return 'В этой беседе нет ников.'
    await event.answer(result, disable_mentions=True)


@bot.message_handler(filters.TextStartswithFilter("ник"))
async def name(event: SimpleBotEvent):
    if event.from_id in banned_nicks:
        return f'Ваш ник изменить нельзя, {BotDB.get_name(event.from_id, event.peer_id)}.'
    name = " ".join(event.text.split(' ')[1:])
    if len(name) >= 16:
        return 'Слишком длинный ник.'
    if name == '':
        if BotDB.user_exists(event.from_id, event.peer_id):
            return f"Ваше имя: {BotDB.get_name(event.from_id, event.peer_id)}"
        else:
            return f'У вас нет ника в этой беседе, {(await vk.users.get(user_ids=event.from_id)).response[0].first_name}'
    if BotDB.user_exists(event.from_id, event.peer_id):
        BotDB.update_user(user_id=event.from_id, name=name, peer_id=event.peer_id)
    else: 
        BotDB.add_user(name=name, peer_id=event.peer_id, user_id=event.from_id)
    return f'Ваше имя изменено, {name}!'


@bot.message_handler(filters.TextContainsFilter("мосич"))
async def mosi4(event: SimpleBotEvent):
    text = event.text
    if not len(text.split(' ')) == 1 and text.split(' ')[1] != '1':
        if text.split(' ')[1].endswith('1') and not text.split(' ')[1].endswith(('11')):
            mad_suff = ''
        elif text.split(' ')[1].endswith(('2', '3', '4')) and not text.split(' ')[1].endswith(('12', '13', '14', '15', '16', '17', '18', '19')):
            mad_suff = 'а'
        else:
            mad_suff = 'ей'
        try:
            int(text.split(' ')[1])
        except ValueError:
            await event.answer(attachment=random.choice(mosi4_list))
            return
        if int(text.split(' ')[1]) <= 10 and text.split(' ')[1] != '0':
            await event.answer(attachment=random.sample(mosi4_list, int(text.split(' ')[1])))
        else:
            await event.reply(attachment=random.choice(mosi4_list), message=f'Как я тебе отправлю {text.split(" ")[1]} мосич{mad_suff}? Держи одного.')
    else:
        await event.answer(attachment=random.choice(mosi4_list))


@bot.message_handler(filters.TextFilter("обнова"))
async def update(event: SimpleBotEvent):
    if event.from_id in admin_list:
        try:
            updater()
            return 'Обновление прошло успешно.'
        except Exception as e:
            await event.reply(f'Что-то конкретно пошло не по плану.\n{e}')
    else:
        await event.reply('Вы не админ.')


@bot.message_handler(filters.TextFilter("команды"))
async def state(event: SimpleBotEvent):
    if BotDB.user_exists(event.from_id, event.peer_id):
        name = BotDB.get_name(event.from_id, event.peer_id)
    else:
        name = (await vk.users.get(user_ids=event.from_id)).response[0].first_name
    state = f'Привет, {name}! Вот список команд бота:\n\nМут (минуты) (с ответом на сообщение) - замутить человека, на чьё сообщение ответили.\n!бот - написать или отправить картинку от имени бота\nКулич - отправляет сообщение Кулича\nКот\Кошка - отправляет фото котика :з\nМут лист - список замученных пользователей\nРазмут (порядковый номер из списка) - размутить пользователя\nНик (имя) - изменить своё имя в конкретной беседе\nНики - список никнеймов в данной беседе\nМосич - отправляет фото Мосича\nОбнова - производит обновление базы картинок в боте\n\nСпасибо, что используете бота!'
    return state


# финальная проверка
@bot.message_handler()
async def main(event: SimpleBotEvent):
    if q_from_id[event.peer_id] == event.from_id:
        q_count[event.peer_id] += 1
    else:
        q_from_id[event.peer_id] = event.from_id
        q_count[event.peer_id] = 1
    counter[event.peer_id] += 1
    if (random.randrange(1, 150) == 40) or ('ку' in event.text.lower()) or (q_count[event.peer_id] % 10 == 0) or (q_count[event.peer_id] >= 25):
        if BotDB.user_exists(event.from_id, event.peer_id):
            name = BotDB.get_name(event.from_id, event.peer_id)
        else:
            name = (await vk.users.get(user_ids=event.from_id)).response[0].first_name
        if q_count[event.peer_id] % 10 == 0:
            return f'{name.upper()} НЕ ФЛУДИ'
        elif q_count[event.peer_id] >= 25:
            try:
                await vk.messages.remove_chat_user(chat_id=event.peer_id-2000000000, user_id=event.from_id)
                q_count[event.peer_id] = 0
                return
            except Exception as e:
                q_count[event.peer_id] = 0
                return f'Что-то конкретно пошло не по плану.\n{e}'
        else:
            return f'{name} ку'
    if (random.randrange(1, 150) == 40) and event.text != '':
        return event.text.upper()
bot.run_forever()