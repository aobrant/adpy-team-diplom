from random import randrange
import configparser
import vk_api
from vk_api.keyboard import VkKeyboard,VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType



config = configparser.ConfigParser()
config.read("settings.ini")
vk_token = config["VK"]["vk_token"]

vk = vk_api.VkApi(token=vk_token)
longpoll = VkLongPoll(vk)

def write_msg(user_id,message):

    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Привет', color=VkKeyboardColor.NEGATIVE)


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            request = event.text

            if request == "привет":
                write_msg(event.user_id, f"Хай, {event.user_id}")
            elif request == "пока":
                write_msg(event.user_id, "Пока((")
            else:
                write_msg(event.user_id, "Не поняла вашего ответа...")




