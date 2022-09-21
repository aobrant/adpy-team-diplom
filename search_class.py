import requests
import configparser
from pprint import pprint


#def find_big_photo(photos):
    #for photo in photos:
        #if photo['type'] == 'w':
            #return photo['type'], photo['url']
    #return photos[-1]['type'], photos[-1]['url']


class VkApi:
    def __init__(self, token: str):
        self.params = {
            'access_token': token,
            'v': '5.131'
        }

    def search(self, **kwargs):
        data = self.users_search(**kwargs)
        result = []
        for item in data:
            if not item.get('is_closed', True):
                # print(item['id'], item['first_name'], item['last_name'], item.get('bdate', ''), item.get('city', ''), )
                photos = self.find_photos(item['id'])
                photos = sorted(photos, key=lambda x: x['likes']['count'])
                photos = photos[-1:-4:-1]
                photos_urls = []
                for photo in photos:
                    photos_urls.append(photo['sizes'][-1]['url'])
                # print(photos_urls)
                result.append({'id': item['id'],
                               'first_name': item['first_name'],
                               'last_name': item['last_name'],
                               'photo_urls': photos_urls})
        return (result)

    def users_search(self, **kwargs):

        vk_url = 'https://api.vk.com/method/users.search'
        params = kwargs | {'has_photo' : 1}
        req = requests.get(vk_url, self.params | params)
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
            'photo_sizes': '1',
            'count': 100
        }
        req = requests.get(url, self.params | params)
        if 'error' in req.json():
            print(req.json()['error']['error_msg'])
            return False
        return req.json()['response']['items']


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("settings.ini")
    vk_token = config["VK"]["vk_token"]
    searcher = VkApi(vk_token)
    res = searcher.search(hometown='Калининград', sex=1, birth_year=1985)  # по году рождения
    #res = searcher.search(hometown='Калининград', sex=1, age_from=20, age_to=25)  # по возрасту
    pprint(res)
