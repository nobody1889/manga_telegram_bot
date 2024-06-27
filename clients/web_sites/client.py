import httpx
from clients.commons import Js_worker, Requests
import asyncio
from bs4 import BeautifulSoup


def manhwax(soup: BeautifulSoup, data: dict) -> dict:
    chapters = soup.find('div', {"class": "eplister", "id": "chapterlist"}).find('ul').find_all('li')

    data["all_chapters"].clear()
    for chapter in chapters:
        data["all_chapters"].append(chapter.find('a')['href'])

    data["name"] = soup.find('h1', {"class": "entry-title", "itemprop": "name"}).text
    data["rate"] = float(soup.find('div', {"class": "num", "itemprop": "ratingValue"}).text)
    data["cover_url"] = soup.find('img', {'class': 'attachment- size- wp-post-image', 'alt': data["name"]})['src']

    return data


def mangahentai(soup: BeautifulSoup, data: dict) -> dict:
    chapters = soup.find('div', {"class": "eplister", "id": "chapterlist"}).find('ul').find_all('li')

    data["all_chapters"].clear()
    for chapter in chapters:
        data["all_chapters"].append(chapter.find('a')['href'])

    data["name"] = soup.find('h1').text.split('\n')[-1]
    data["rate"] = float(soup.find("span", class_="score font-meta total_votes").text) * 2
    data["cover_url"] = soup.find('img', class_="img-responsive")['src']

    return data


class Client:
    def __init__(self, name: str):
        self._new_chapters_dict = {}
        self.__comics_res = None
        self.urls = None
        self.name = name
        self._setter()

    def _setter(self):
        self.user = Js_worker(name=self.name)
        if data := self.user.read():
            self.urls = list(data.keys())
            self.data: dict = data
        else:
            raise Exception('invalid person')

    async def _each_page(self, page: httpx.Client().get):
        url = str(page.url)
        url_type = url.split('/')[2].split('.')[0]
        soup = BeautifulSoup(page.content, 'lxml')

        match url_type:
            case 'manhwax':
                self.data[url] = manhwax(soup, data=self.data[url])
            case 'mangahentai':
                self.data[url] = mangahentai(soup, data=self.data[url])

        last_one = self.data[url]["last_chapter"]
        last_chapter = self.data[url]["last_chapter"] = self.data[url]["all_chapters"][0]

        if last_one:
            num = int(float(last_chapter.split('/')[-2].split('-')[-2]) - float(last_one.split('/')[-2].split('-')[-2]))
            if num > 0:
                self.data[url]["new_chapters"] = self.data[url]["all_chapters"][:num]
                self._new_chapters_dict[url] = self.data[url]["all_chapters"][:num]
            else:
                self.data[url]["new_chapters"] = []

    async def main_pages_update(self):
        self.__comics_res = await Requests().aget(self.urls)
        tasks = [self._each_page(page) for page in self.__comics_res]
        await asyncio.gather(*tasks)

    def write_data(self):
        self.user.write(data=self.data)

    def new_chapters(self):
        return self._new_chapters_dict

    async def run(self):
        await self.main_pages_update()


__all__ = ('Client',)
