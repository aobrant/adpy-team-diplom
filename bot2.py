from random import randrange
import configparser
import vk_api
from vk_api.keyboard import VkKeyboard,VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from search_class import VkApi
from pprint import pprint



config = configparser.ConfigParser()
config.read("settings.ini")
vk_token = config["VK"]["vk_token"]
user_token = config["VK"]["user_token"]
searcher = VkApi(vk_token, user_token)

vk = vk_api.VkApi(token=vk_token)
longpoll = VkLongPoll(vk)

def write_msg(user_id, message, attachment=None, keyboard=None):

    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),
                                'attachment': attachment, 'keyboard': keyboard})

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Привет', color=VkKeyboardColor.NEGATIVE)


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        user_info = searcher.get_info_by_id(event.user_id)
        bdate = user_info['bdate']
        year = int(bdate.split('.')[2])
        #print(f'year = {year}')
        city_id = user_info['city']['id']
        #print(f'city_id = {city_id}')
        sex = user_info['sex']
        #print(f'sex = {sex}')
        sex = 1 if sex == 2 else 2
        res = searcher.search(city=city_id, sex=1, birth_year=year)
        #pprint(res)

        if event.to_me:
            request = event.text
            print(request)

            if request == "привет":
                write_msg(event.user_id, f"Хай, {event.user_id}")
            elif request == "пока":
                write_msg(event.user_id, "Пока((")
            elif request.isdigit():
                n = int(request)
                write_msg(event.user_id,
                          f"{res[n]['first_name']} {res[n]['last_name']}\nhttps://vk.com/id{res[n]['id']}",
                          searcher.find_3_photos(res[n]['id']))
            elif 'поиск' in request:
                write_msg(event.user_id, f"{res[0]['first_name']} {res[0]['last_name']}\nhttps://vk.com/id{res[0]['id']}",
                          searcher.find_3_photos(res[0]['id']))
            else:
                write_msg(event.user_id, "Не поняла вашего ответа...Напиши номер пары числом, начни с 0, как программист")
