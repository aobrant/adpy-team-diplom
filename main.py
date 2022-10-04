import configparser
import sqlalchemy
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from datetime import datetime
from random import randrange
from sqlalchemy.orm import sessionmaker

from search_class import VkApi
from bd_models import create_tables, User_stranger, User, Stranger

config = configparser.ConfigParser()
config.read("settings.ini")
vk_token = config["VK"]["vk_token"]
user_token = config["VK"]["user_token"]
group_id = config["VK"]["group_id"]
db_login = config['postgres']['db_login']
db_password = config['postgres']['db_password']
db_url = config['postgres']['db_url']

DSN = f'postgresql://{db_login}:{db_password}@{db_url}'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

searcher = VkApi(vk_token, user_token)

vk = vk_api.VkApi(token=vk_token)
longpoll = VkBotLongPoll(vk, group_id=group_id)

state = dict()


def write_msg(user_id, message, attachment=None, keyboard=None):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),
                                'attachment': attachment, 'keyboard': keyboard})


keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Параметры', color=VkKeyboardColor.SECONDARY)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:

        id = event.object['message']['from_id']

        if event:
            request = event.object['message']['text'].lower()
            print(request)
            if request == "привет" or request == "начать":
                inline_keyboard = VkKeyboard(one_time=False, inline=True)
                inline_keyboard.add_button(label="Like")
                first_name = searcher.get_info_by_id(id)['first_name']
                write_msg(id,
                          f"Привет, {first_name}, меня зовут Лаура! "
                          f"Я - бот для знакомств, давай начнем поиск подходящей пары. Для поиска напиши ПОИСК",
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
                        name = q2.name
                        year = q2.year
                        user_sex = q2.sex
                        city = q2.city
                        search_city = q2.search_city
                        city_id = q2.city_id
                        age_from = q2.age_from
                        age_to = q2.age_to
                    else:
                        user_info = searcher.get_info_by_id(id)
                        name = ' '.join((user_info.get('first_name', ''), user_info.get('last_name', '')))
                        bdate = user_info['bdate']
                        birthday = datetime.strptime(bdate, '%d.%m.%Y')
                        age = int((datetime.now() - birthday).days / 365.2425)
                        age_from = age
                        age_to = age
                        year = int(bdate.split('.')[2])
                        city = user_info['city']['title']
                        search_city = user_info['city']['title']
                        city_id = user_info['city']['id']
                        user_sex = user_info['sex']
                        user = User(id=id, name=name, year=year, sex=user_sex, city=city, city_id=city_id,
                                    age_from=age_from, age_to=age_to, search_city=search_city)
                        session.add_all([user])
                        session.commit()
                    if user_sex == 2 or user_sex == (2,):
                        sex = 1
                    elif user_sex == 1 or user_sex == (1,):
                        sex = 2
                    else:
                        print('Ошибка определения пола')
                        sex = 0
                    res = searcher.search(hometown=search_city, sex=sex, age_from=age_from, age_to=age_to)
                    print(f'search_city = {search_city}, sex = {sex}, age_from = {age_from}, age_to = {age_to}')
                    print(f'len(res) = {len(res)}')
                    strangers, user_strangers = [], []
                    for user_info in res:
                        stranger_id = user_info['id']
                        q = session.query(Stranger).get(stranger_id)
                        if q:
                            q3 = session.query(User_stranger).filter(
                                User_stranger.user_id == id,
                                User_stranger.stranger_id == stranger_id
                            ).all()
                            if not q3:
                                user_stranger = User_stranger(user_id=id, stranger_id=stranger_id, status='W')
                                user_strangers.append(user_stranger)
                        else:
                            stranger = Stranger(id=stranger_id,
                                                name=' '.join((user_info['first_name'], user_info['last_name'])))
                            strangers.append(stranger)
                            user_stranger = User_stranger(user_id=id, stranger_id=stranger_id, status='W')
                            user_strangers.append(user_stranger)

                    session.add_all(strangers)
                    session.commit()
                    session.add_all(user_strangers)
                    session.commit()
                    q = session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).filter(
                        User_stranger.user_id == id,
                        User_stranger.status == 'W'
                    ).limit(1).all()
                    if not q:
                        write_msg(id, 'Никого нового не найдено')
                for el in q:
                    name = el.name
                    stranger_id = el.id
                    inline_keyboard = VkKeyboard(one_time=False, inline=True)
                    inline_keyboard.add_callback_button("Добавить в избранное",
                                                        color=VkKeyboardColor.POSITIVE,
                                                        payload={"type": "Like " + str(stranger_id)},)
                    inline_keyboard.add_callback_button("Добавить в черный список",
                                                        color=VkKeyboardColor.NEGATIVE,
                                                        payload={"type": "Black " + str(stranger_id)}, )
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
                    inline_keyboard.add_callback_button("Добавить в черный список",
                                                        color=VkKeyboardColor.NEGATIVE,
                                                        payload={"type": "Black " + str(stranger_id)}, )
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

            elif 'параметры' in request:
                q2 = session.query(User).get(id)
                if q2:
                    name = q2.name
                    year = q2.year
                    user_sex = q2.sex
                    city = q2.city
                    search_city = q2.search_city
                    city_id = q2.city_id
                    age_from = q2.age_from
                    age_to = q2.age_to
                else:
                    user_info = searcher.get_info_by_id(id)
                    # name = ' '.join((user_info['first_name'], user_info['last_name']))
                    name = ' '.join((user_info.get('first_name', ''), user_info.get('last_name', '')))
                    bdate = user_info['bdate']
                    birthday = datetime.strptime(bdate, '%d.%m.%Y')
                    age = int((datetime.now() - birthday).days / 365.2425)
                    age_from = age
                    age_to = age
                    year = int(bdate.split('.')[2])
                    city = user_info['city']['title']
                    search_city = user_info['city']['title']
                    city_id = user_info['city']['id']
                    user_sex = user_info['sex']
                    user = User(id=id, name=name, year=year, sex=user_sex, city=city, city_id=city_id,
                                age_from=age_from, age_to=age_to, search_city=city)
                    session.add_all([user])
                    session.commit()
                inline_keyboard = VkKeyboard(one_time=False, inline=True)
                inline_keyboard.add_callback_button("Возраст от", color=VkKeyboardColor.PRIMARY,
                                                    payload={"type": "age_from"}, )
                inline_keyboard.add_callback_button("Возраст до", color=VkKeyboardColor.PRIMARY,
                                                    payload={"type": "age_to"}, )
                inline_keyboard.add_callback_button("Город", color=VkKeyboardColor.PRIMARY,
                                                    payload={"type": "search_city"}, )
                write_msg(id,
                          f"Возраст от {age_from} до {age_to}\nГород: {search_city}",
                          keyboard=inline_keyboard.get_keyboard()
                          )
                state[id] = None

            elif state.get(id) == 'age_from':
                if request.isdigit():
                    age_from = int(request)
                    session.query(User).filter(User.id == id).update({"age_from": age_from})
                    session.query(User_stranger).filter(User_stranger.status == "W").delete()
                    session.commit()
                    write_msg(id, "OK")
                else:
                    write_msg(id, "Напишите желаемый максимальный возраст числом")

            elif state.get(id) == 'age_to':
                if request.isdigit():
                    age_to = int(request)
                    session.query(User).filter(User.id == id).update({"age_to": age_to})
                    session.query(User_stranger).filter(User_stranger.status == "W").delete()
                    session.commit()
                    write_msg(id, "OK")
                else:
                    write_msg(id, "Напишите желаемый максимальный возраст числом")

            elif state.get(id) == 'search_city':
                search_city = event.object['message']['text']
                session.query(User).filter(User.id == id).update({"search_city": search_city})
                session.query(User_stranger).filter(User_stranger.status == "W").delete()
                session.commit()
                write_msg(id, "OK")

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
            q2 = session.query(Stranger).get(stranger_id)
            name = q2.name
            inline_keyboard = VkKeyboard(one_time=False, inline=True)
            inline_keyboard.add_callback_button("Убрать из избранного",
                                                color=VkKeyboardColor.NEGATIVE,
                                                payload={"type": "Delete " + str(stranger_id)}, )
            inline_keyboard.add_callback_button("Добавить в черный список",
                                                color=VkKeyboardColor.NEGATIVE,
                                                payload={"type": "Black " + str(stranger_id)}, )
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
            q2 = session.query(Stranger).get(stranger_id)
            name = q2.name
            inline_keyboard = VkKeyboard(one_time=False, inline=True)
            inline_keyboard.add_callback_button("Добавить в избранное",
                                                color=VkKeyboardColor.POSITIVE,
                                                payload={"type": "Like " + str(stranger_id)}, )
            inline_keyboard.add_callback_button("Добавить в черный список",
                                                color=VkKeyboardColor.NEGATIVE,
                                                payload={"type": "Black " + str(stranger_id)}, )
            last_id = vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message=f"{name}\nhttps://vk.com/id{stranger_id}",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=inline_keyboard.get_keyboard(),
                attachment=searcher.find_3_photos(stranger_id),
            )

        elif 'Black' in event.object.payload.get("type"):
            stranger_id = int(event.object.payload.get("type").split()[1])
            session.query(User_stranger).filter(User_stranger.stranger_id == stranger_id,
                                                User_stranger.user_id == id).update({"status": "B"})
            session.commit()
            last_id = vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message='Добавлено в черный список',
                conversation_message_id=event.obj.conversation_message_id,
            )

        elif 'age_from' in event.object.payload.get("type"):
            vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message='Напишите желаемый минимальный возраст числом',
                conversation_message_id=event.obj.conversation_message_id,
            )
            state[id] = 'age_from'

        elif 'age_to' in event.object.payload.get("type"):
            vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message='Напишите желаемый максимальный возраст числом',
                conversation_message_id=event.obj.conversation_message_id,
            )
            state[id] = 'age_to'

        elif 'search_city' in event.object.payload.get("type"):
            vk.get_api().messages.edit(
                peer_id=event.obj.peer_id,
                message='Напишите желаемый город',
                conversation_message_id=event.obj.conversation_message_id,
            )
            state[id] = 'search_city'
