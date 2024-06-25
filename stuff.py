from clients.commons import Js_worker
from clients.manhwax import Client

valid_sites = [
    'https://manhwax.org',
    'https://hentaiwebtoon.com',
]


def valid_urls(url: str):
    urls = url.split('\n')

    my_valid_urls = [u for vs in valid_sites for u in urls if vs in u and not vs == u]

    my_invalid_urls = [u for u in urls if u not in my_valid_urls]

    return my_valid_urls, my_invalid_urls


def add_url(urls: str, user: str):
    valid, invalid = valid_urls(urls)
    if valid:
        Js_worker(user).update(urls=valid)
    return valid, invalid


def remove_url(urls: str, user):
    person = Js_worker(user)
    if person.read():
        data: dict | None = person.read()

        if data:
            valid, invalid = valid_urls(urls)
            for v in valid:
                data.pop(v)
            person.write(data=data)
            return valid, invalid

    return None, None


async def search_new(user: str) -> dict:
    person = Client(name='5519596138')
    await person.run()
    person.write_data()
    news: dict = person.new_chapters()
    return news
