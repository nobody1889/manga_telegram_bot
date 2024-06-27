import os
import json


class Js_worker:
    def __init__(self, name: str):
        print(f'user: {name} working now')
        self._name = name.lower()
        one = os.getcwd()
        self.__path: str = one + '/js_holder/' + self._name + '.json'

    def check(self):
        if os.path.exists(self.__path):
            return True

        return False

    def read(self) -> dict | None:
        if not self.check():
            return None

        with open(self.__path, 'r') as file:
            what_return = json.load(file)

        return what_return

    def __set_data(self, urls: list[str], data: dict = None):
        if data is None:
            data = {}

        for url in urls:
            local_data = {
                url: {
                    'type': url.split('/')[2].split('.')[0],  # which website
                    'name': '',
                    'cover_url': '',  # cover of the comic
                    'rate': 0,  # rating of comic
                    'last_chapter': '',
                    'all_chapters': [],
                    'new_chapters': []
                },
            }
            data.update(local_data)

        return data

    def write(self, urls: list[str] = None, data: dict = None) -> None:
        if urls is None and data is None:
            raise Exception('at least one of urls or data must have value')

        if data is None:
            data = self.__set_data(urls)

        with open(self.__path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def delete(self):
        os.remove(self.__path + self._name + '.json')

    def update(self, data: dict = None, urls: list[str] = None):
        if data == urls:
            return None

        if not self.check():
            self.write(urls)

        if data := self.read():
            new_data = self.__set_data(urls=urls, data=data)
            self.write(data=new_data)


__all__ = ("Js_worker",)
