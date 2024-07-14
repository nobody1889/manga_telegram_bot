import httpx
from clients.commons import Js_worker, Requests
import asyncio
from bs4 import BeautifulSoup

from clients.web_sites.web_clients import Manhwax, Chapmanganato, Comixextra


class Client:
    def __init__(self, name: str, urls: list[str] = None):
        self._new_chapters_dict = {}
        self.__comics_res = None
        self.urls = urls
        self.name = name
        self._setter()

    def _setter(self):
        self.user = Js_worker(name=self.name)
        if data := self.user.read():
            if self.urls is None:
                self.urls = list(data.keys())
            self.data: dict = data
        else:
            raise ValueError('invalid person')

    async def _each_page(self, page: httpx.Client().get):
        url = str(page.url)
        url_type = url.split('/')[2].split('.')[0]
        soup = BeautifulSoup(page.content, 'lxml')

        match url_type:
            case 'manhwax':
                self.data[url] = Manhwax.comic_main_page(soup, data=self.data[url])
            case 'chapmanganato':
                self.data[url] = Chapmanganato.comic_main_page(soup, data=self.data[url])
            case 'comixextra':
                self.data[url] = Comixextra.comic_main_page(soup, data=self.data[url])

        last_one = self.data[url]["last_chapter"]

        if last_one:
            all_chapters_len = len(self.data[url]["all_chapters"])
            num = self.data[url]["all_chapters"].index(last_one)

            if (all_chapters_len - num) > 0:
                self.data[url]["new_chapters"] = self.data[url]["all_chapters"][:num]
                self._new_chapters_dict[self.data[url]["name"]] = self.data[url]["all_chapters"][:num]

            else:
                self.data[url]["new_chapters"] = []
        else:
            self.data[url]["new_chapters"] = []

        self.data[url]["last_chapter"] = self.data[url]["all_chapters"][0]

    async def main_pages_update(self):
        self.__comics_res = await Requests().aget(self.urls)
        tasks = [self._each_page(page) for page in self.__comics_res]
        await asyncio.gather(*tasks)

    def write_data(self):
        self.user.write(data=self.data)

    def new_chapters(self):
        return self._new_chapters_dict

    def get(self) -> tuple:
        urls: list = []
        for d in self.data:
            urls.append(d)
        return urls, self.data

    async def run(self):
        await self.main_pages_update()


__all__ = ('Client',)
