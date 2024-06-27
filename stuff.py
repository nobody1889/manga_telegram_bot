from clients.commons import Js_worker
from clients.web_sites import Client

valid_sites = [
    'https://manhwax.org',
    # 'https://hentaiwebtoon.com',
    # 'https://www.mangaread.org/'
    # 'https://madaradex.org/',
    'https://chapmanganato.to/',
    'https://comixextra.com/',
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
    person = Client(name=user)
    await person.run()
    person.write_data()
    news: dict = person.new_chapters()
    return news


def show_comics(name: str) -> str:
    person = Client(name=name)
    my_comics = person.get()
    text = ''
    for num, my_comic in enumerate(my_comics):
        text += str(num) + '. ' + str(my_comic) + '\n'
    return text
