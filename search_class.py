import requests
import configparser
from pprint import pprint


class VkApi:
    def __init__(self, token: str, user_token=None):
        self.params = {
            'access_token': token,
            'v': '5.131'
        }
        self.user_params = {
            'access_token': user_token,
            'v': '5.131'
        }

    def search(self, **kwargs):
        data = self.users_search(**kwargs)
        result = []
        for item in data:
            if not item.get('is_closed', True):
                # print(item['id'], item['first_name'], item['last_name'], item.get('bdate', ''), item.get('city', ''), )
                #photos = self.find_photos(item['id'])
                #pprint(photos)
                #photos = sorted(photos, key=lambda x: x['likes']['count'])
                #photos = photos[-1:-4:-1]
                #photos_urls = []
                #for photo in photos:
                    #photos_urls.append(f"photo{photo['owner_id']}_{photo['id']}")
                # print(photos_urls)
                result.append({'id': item['id'],
                               'first_name': item['first_name'],
                               'last_name': item['last_name']})
                               #'photo_urls': photos_urls})
        return (result)

    def users_search(self, **kwargs):

        vk_url = 'https://api.vk.com/method/users.search'
        params = kwargs | {'has_photo' : 1,
                           'count' : 1000,
                           'status' : 6 #  в активном поиске
                           }
        req = requests.get(vk_url, self.user_params | params)
        # print(req)
        # pprint(req.json())
        if 'error' in req.json():
            print(req.json()['error']['error_msg'])
            return
        result = req.json()['response']['items']
        # pprint(result)
        return result

    def find_photos(self, id):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': id,
            'album_id': 'profile',
            'extended': '1',
            #'photo_sizes': '1',
            'count': 100
        }
        req = requests.get(url, self.user_params | params)
        if 'error' in req.json():
            print(req.json()['error']['error_msg'])
            return False
        #pprint(req.json()['response']['items'])
        return req.json()['response']['items']

    def find_3_photos(self, id):
        photos = self.find_photos(id)
        photos = sorted(photos, key=lambda x: x['likes']['count'])
        photos = photos[-1:-4:-1]
        photos_urls = []
        for photo in photos:
            photos_urls.append(f"photo{photo['owner_id']}_{photo['id']}")
        res = ','.join(photos_urls)
        return res

    def get_info_by_id(self, user_id):
        url = 'https://api.vk.com/method/users.get'
        params = {
            'user_ids': user_id,
            'fields' : 'bdate, city, sex'
        }
        req = requests.get(url, self.params | params)
        if 'response' not in req.json():
            return False
        #pprint(req.json()['response'][0])
        return req.json()['response'][0]


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("settings.ini")
    vk_token = config["VK"]["vk_token"]
    user_token = config["VK"]["user_token"]
    searcher = VkApi(vk_token, user_token)
    #res = searcher.search(hometown='Екатеринбург', sex=1, birth_year=1985)  # по году рождения
    #res = searcher.search(hometown='Калининград', sex=1, age_from=20, age_to=25)  # по возрасту
    res = searcher.search(city=49, sex=1, birth_year=1985)  # по году рождения и id города
    pprint(res)
    print(f'len = {len(res)}')
