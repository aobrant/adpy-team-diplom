from random import randrange
import configparser
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from search_class import VkApi
from pprint import pprint

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from bd_models import create_tables, User_stranger, User, Stranger

DSN = 'postgresql://postgres:postgres@localhost:5432/netology_db'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()


config = configparser.ConfigParser()
config.read("settings.ini")
vk_token = config["VK"]["vk_token"]
user_token = config["VK"]["user_token"]
searcher = VkApi(vk_token, user_token)

vk = vk_api.VkApi(token=vk_token)
#longpoll = VkLongPoll(vk)
longpoll = VkBotLongPoll(vk, group_id='216157132')

def write_msg(user_id, message, attachment=None, keyboard=None):

    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),
                                'attachment': attachment, 'keyboard': keyboard})


keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)

for event in longpoll.listen():
    pprint(event)
    if event.type == VkBotEventType.MESSAGE_NEW:

        def get_name(uid: int) -> str:
            data = vk.method("users.get", {"user_ids": uid})[0]
            return f"{data['first_name']}"

        #id = event.user_id
        id = event.object['message']['from_id']

        if event:
            request = event.object['message']['text'].lower()
            print(request)
            if request == "привет":
                inline_keyboard = VkKeyboard(one_time=False, inline=True)
                inline_keyboard.add_button(label="Like")
                write_msg(id,
                          f"Привет, {get_name(id)}, меня зовут Лаура! Я - бот для знакомств, давай начнем поиск подходящей пары. Для поиска напиши ПОИСК",
                          keyboard=keyboard.get_keyboard())
            elif request == "пока":
                write_msg(event.user_id, "Пока((")
            elif 'поиск' in request:
                q = session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).filter(
                    User_stranger.user_id == id,
                    User_stranger.status == 'W'
                ).limit(1).all()
                if not q:
                    print('Запускаем новый поиск')
                    q2 = session.query(User).get(id)
                    if q2:
                        name = q2.name,
                        year = q2.year,
                        sex = q2.sex,
                        city = q2.city,
                        city_id = q2.city_id
                    else:
                        user_info = searcher.get_info_by_id(id)
                        # name = ' '.join((user_info['first_name'], user_info['last_name']))
                        name = ' '.join((user_info.get('first_name', ''), user_info.get('last_name', '')))
                        bdate = user_info['bdate']
                        year = int(bdate.split('.')[2])
                        city = user_info['city']['title']
                        city_id = user_info['city']['id']
                        sex = user_info['sex']
                        user = User(id=id, name=name, year=year, sex=sex, city=city, city_id=city_id)
                        session.add_all([user])
                        session.commit()
                    sex = 1 if sex == 2 else 2
                    res = searcher.search(city=city_id, sex=sex, birth_year=year)
                    strangers, user_strangers = [], []
                    for user_info in res:
                        stranger_id = user_info['id']
                        q = session.query(Stranger).get(stranger_id)
                        if q:
                            pass
                        else:
                            stranger = Stranger(id=stranger_id,
                                                name=' '.join((user_info['first_name'], user_info['last_name'])),
                                                year=year, sex=sex, city=city, city_id=city_id)
                            # year, sex, city, city_id - не нужны в базе
                            strangers.append(stranger)
                            user_stranger = User_stranger(user_id=id, stranger_id=stranger_id, status='W')
                            user_strangers.append(user_stranger)

                    session.add_all(strangers)
                    session.add_all(user_strangers)
                    session.commit()
                    q = session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).filter(
                        User_stranger.user_id == id,
                        User_stranger.status == 'W'
                    ).limit(1).all()
                for el in q:
                    name = el.name
                    stranger_id = el.id
                    inline_keyboard = VkKeyboard(one_time=False, inline=True)
                    inline_keyboard.add_callback_button("Добавить в избранное",
                                                        color=VkKeyboardColor.POSITIVE,
                                                        payload={"type": "Like " + str(stranger_id)},)
                    write_msg(id,
                              f"{name}\nhttps://vk.com/id{stranger_id}",
                              searcher.find_3_photos(stranger_id),
                              inline_keyboard.get_keyboard())
                    session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                        User_stranger.user_id == id).update({"status": "S"})
                    session.commit()

            elif 'like' in request:
                stranger_id = int(request.split()[1])
                session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                    User_stranger.user_id == id).update({"status": "L"})
                session.commit()
                write_msg(id, "Добавлено в избранное")

            elif 'избранное' in request:
                q = session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).filter(
                    User_stranger.user_id == id,
                    User_stranger.status == 'L'
                ).all()
                for el in q:
                    name = el.name
                    stranger_id = el.id
                    inline_keyboard = VkKeyboard(one_time=False, inline=True)
                    inline_keyboard.add_callback_button("Убрать из избранного",
                                                        color=VkKeyboardColor.NEGATIVE,
                                                        payload={"type": "Delete " + str(stranger_id)}, )
                    write_msg(id,
                              f"{name}\nhttps://vk.com/id{stranger_id}",
                              searcher.find_3_photos(stranger_id),
                              inline_keyboard.get_keyboard()
                              )


            elif 'delete' in request:
                stranger_id = int(request.split()[1])
                session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                    User_stranger.user_id == id).update({"status": "S"})
                session.commit()
                write_msg(id, "Удалено из избранного")

            else:
                write_msg(id, "Не поняла вашего ответа...Для поиска напиши ПОИСК",
                          keyboard=keyboard.get_keyboard())
    elif event.type == VkBotEventType.MESSAGE_EVENT:
        id = event.object['user_id']
        if 'Like' in event.object.payload.get("type"):
            stranger_id = int(event.object.payload.get("type").split()[1])
            session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                User_stranger.user_id == id).update({"status": "L"})
            session.commit()
            inline_keyboard = VkKeyboard(one_time=False, inline=True)
            inline_keyboard.add_callback_button("Убрать из избранного",
                                                color=VkKeyboardColor.NEGATIVE,
                                                payload={"type": "Delete " + str(stranger_id)}, )
            last_id = vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message=f"{name}\nhttps://vk.com/id{stranger_id}",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=inline_keyboard.get_keyboard(),
                attachment=searcher.find_3_photos(stranger_id),
            )
        elif 'Delete' in event.object.payload.get("type"):
            stranger_id = int(event.object.payload.get("type").split()[1])
            session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                User_stranger.user_id == id).update({"status": "S"})
            session.commit()
            inline_keyboard = VkKeyboard(one_time=False, inline=True)
            inline_keyboard.add_callback_button("Добавить в избранное",
                                                color=VkKeyboardColor.POSITIVE,
                                                payload={"type": "Like " + str(stranger_id)}, )
            last_id = vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message=f"{name}\nhttps://vk.com/id{stranger_id}",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=inline_keyboard.get_keyboard(),
                attachment=searcher.find_3_photos(stranger_id),
            )
