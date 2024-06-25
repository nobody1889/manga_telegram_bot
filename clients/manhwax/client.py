import httpx
from clients.commons import Js_worker, Requests
import asyncio
from bs4 import BeautifulSoup


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
        soup = BeautifulSoup(page.content, 'lxml')

        chapters = soup.find('div', {"class": "eplister", "id": "chapterlist"}).find('ul').find_all('li')
        for chapter in chapters:
            self.data[url]["all_chapters"].append(chapter.find('a')['href'])
        self.data[url]["name"] = soup.find('h1', {"class": "entry-title", "itemprop": "name"}).text
        self.data[url]["rate"] = float(soup.find('div', {"class": "num", "itemprop": "ratingValue"}).text)
        self.data[url]["cover_url"] = soup.find('img', {'class': 'attachment- size- wp-post-image',
                                                        'alt': self.data[url]["name"]})['src']

        last_one = self.data[url]["last_chapter"]
        last_chapter = self.data[url]["last_chapter"] = self.data[url]["all_chapters"][0]

        if not self.data[url]["name"]:
            self.data[url]["name"] = url.split('/')[-2].replace('-', ' ')
            self.data[url]["type"] = url.split('/')[2].split('.')[0]
            self.data[url]["new_chapters"] = list(self.data[url]["last_chapter"])

        else:
            if last_one:
                num = int(
                    float(last_chapter.split('/')[-2].split('-')[-2]) - float(last_one.split('/')[-2].split('-')[-2]))

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


if __name__ == '__main__':
    person = Client(name='5519596138')
    person.write_data()
