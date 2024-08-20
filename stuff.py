import os

from clients.commons import Js_worker
from clients.web_sites import Client
from clients.web_sites.web_clients import valid_sites


def check(name: str):
    one = os.getcwd()
    path: str = one + '/js_holder/' + name + '.json'
    if os.path.exists(path):
        return True

    return False


def valid_urls(url: str):
    urls = url.split('\n')

    my_valid_urls = [u for vs in valid_sites for u in urls if vs in u and not vs == u]

    my_invalid_urls = [u for u in urls if u not in my_valid_urls]

    return my_valid_urls, my_invalid_urls


async def add_url(urls: str, user: str):
    valid, invalid = valid_urls(urls)
    if valid:
        Js_worker(user).update(urls=valid)
        await search_new(user, valid)
    return valid, invalid


def remove_url(urls: str, user):
    person = Js_worker(user)
    if urls.lower() == 'remove all':
        person.delete()
        return 'all', None
    elif person.read():
        data: dict | None = person.read()

        if data:
            valid, invalid = valid_urls(urls)
            for v in valid:
                data.pop(v)
            if len(data) == 0:
                person.delete()
            else:
                person.write(data=data)
            return valid, invalid

    return None, None


async def search_new(user: str, urls: list[str] = None) -> dict:
    person = Client(name=user, urls=urls)
    await person.run()
    person.write_data()
    news: dict = person.new_chapters()

    return news


def read_new_from_file(user: str) -> dict:
    if check(user):
        my_dict: dict = {}
        user = Js_worker(name=user)
        if all_data := user.read():
            for data in all_data:
                if all_data[data]["new_chapters"]:
                    my_dict.update({data: all_data[data]})
        return my_dict
    else:
        raise ValueError('Invalid person')


def show_comics(name: str) -> dict:
    person = Client(name=name)
    return person.data
