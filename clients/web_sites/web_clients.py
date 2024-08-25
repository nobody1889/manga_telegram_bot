import json
import re

from bs4 import BeautifulSoup
import httpx

valid_sites = [  # websites we create class(we scraping it) for
    'https://manhwax.org/',
    'https://chapmanganato.to/',
    'https://comixextra.com/',
]

sites = [site.split('/')[-2].split('.')[0] for site in valid_sites]


async def request(url: str, header: dict = None, bfs: bool = True) -> BeautifulSoup | bytes:
    client = httpx.AsyncClient()
    res = await client.get(url, headers=header, timeout=30)

    res.raise_for_status()

    if bfs:
        return BeautifulSoup(res.content, "lxml")
    else:
        return res.content


class BaseWebClass:
    @staticmethod
    def get_chapter_number(url: str) -> float:
        raise NotImplementedError("Not implemented")

    @staticmethod
    def comic_main_page(soup: BeautifulSoup, data: dict) -> dict:
        raise NotImplementedError("Not implemented")

    @staticmethod
    async def new_comics(page: int = 0, comics=None) -> dict:
        raise NotImplementedError("Not implemented")

    async def search(self, text: str, page: int = 0) -> dict:
        raise NotImplementedError("Not implemented")

    @staticmethod
    async def get_comic_images(url: str) -> list[str]:
        raise NotImplementedError("Not implemented")


class Manhwax(BaseWebClass):
    name = "manhwax"
    limit_search: int = 10
    limit_new: int = 20
    get_headers: dict = {}

    @staticmethod
    def get_chapter_number(url: str) -> float:
        text = url.split("/")[-2]
        chapter = text[text.find("chapter-") + len("chapter-"):text.find("-english")]
        try:
            number = float(chapter)
        except ValueError:
            new = chapter.replace("-", ".")
            number = float(new)
        return number

    @staticmethod
    def comic_main_page(soup: BeautifulSoup, data: dict) -> dict:
        chapters = soup.find('div', {"class": "eplister", "id": "chapterlist"}).find('ul').find_all('li')

        data["all_chapters"].clear()
        for chapter in chapters:
            data["all_chapters"].append(chapter.find('a')['href'])

        data["name"] = soup.find('h1', {"class": "entry-title", "itemprop": "name"}).text
        data["rate"] = float(soup.find('div', {"class": "num", "itemprop": "ratingValue"}).text)
        data["status"] = soup.find("div", class_="tsinfo").find("i").text
        all_tags = soup.find("span", class_="mgen").find_all('a')
        data["genres"] = [tag.text for tag in all_tags]
        data["cover_url"] = soup.find('img', {'class': 'attachment- size- wp-post-image', 'alt': data["name"]})['src']

        return data

    @staticmethod
    async def new_comics(page: int = 0, comics=None) -> dict:
        if comics is None:
            if page == 0:
                base_url = "https://manhwax.org/"
            else:
                base_url = f"https://manhwax.org/page/{page + 1}/"

            soup = await request(base_url)
            comics = soup.find_all("div", class_="bs styletere")

        comics_info: dict = {}
        for comic in comics:
            comic_url = comic.find('a')["href"]
            comics_info[comic_url] = {}
            comics_info[comic_url]["name"] = comic.find("div", class_="tt").text
            comics_info[comic_url]["cover"] = comic.find("img")["src"]

        return comics_info

    async def search(self, text: str, page: int = 0) -> dict:
        name = "+".join(text.split(" "))
        search_url = f"https://manhwax.org/page/{page + 1}/?s={name}"
        soup = await request(search_url)

        body = soup.find("div", class_="listupd")
        comics = body.find_all('div', class_="bs")

        if len(comics):
            result_comics: dict = await self.new_comics(comics=comics)
            return result_comics

        else:
            return {}

    @staticmethod
    async def get_comic_images(url: str) -> list[str]:
        def extract_ts_reader_content(script_tags):
            pattern = re.compile(r'<script>.*?ts_reader\.run\((\{.*?\})\);.*?<\/script>', re.DOTALL)
            matches = pattern.findall(script_tags)
            return matches

        soup = await request(url)

        content = soup.find_all('script')
        links = [extract_ts_reader_content(str(one)) for one in content]
        v_link = [v for v in links if v][-1][-1]

        js = json.loads(v_link)
        images = js['sources'][0]['images']
        return images


class Chapmanganato(BaseWebClass):
    name = "chapmanganato"
    limit_search: int = 20
    limit_new: int = 24
    get_headers: dict = {
        "Referer": "https://chapmanganato.to/",
    }

    @staticmethod
    def get_chapter_number(url: str) -> float:
        text = url.split("/")[-2]
        chapter = text[text.find("chapter-") + len("chapter-"):]
        try:
            number = float(chapter)
        except ValueError:
            new = chapter.replace("-", ".")
            number = float(new)
        return number

    @staticmethod
    def comic_main_page(soup: BeautifulSoup, data: dict) -> dict:
        chapters = soup.find("ul", class_="row-content-chapter").find_all('li')

        data["all_chapters"].clear()
        for chapter in chapters:
            data["all_chapters"].append(chapter.find('a')['href'] + '/')

        data["name"] = soup.find('h1').text.split('\n')[-1]
        data["rate"] = float(soup.find('em', {'property': "v:average"}).text) * 2

        all_tags = soup.find("table", class_="variations-tableInfo").find_all("td", class_="table-value")
        data["status"] = all_tags[-2].text
        data["genres"] = [tag.text for tag in all_tags[-1] if tag.text not in [' - ', '\n']]
        data["cover_url"] = soup.find("img", class_="img-loading")['src']

        return data

    @staticmethod
    async def new_comics(page: int = 0, comics=None) -> dict:
        if comics is None:
            if page == 0:
                base_url = f"https://manganato.com/genre-all"
            else:
                base_url = f"https://manganato.com/genre-all/{page + 1}"
            soup = await request(base_url)

            comics = soup.find_all("div", class_="content-genres-item")

        comics_info: dict = {}

        for comic in comics:
            comic_url = comic.find('a')["href"]
            comics_info[comic_url] = {}
            comics_info[comic_url]["name"] = comic.find("h3").text
            comics_info[comic_url]["cover"] = comic.find("img")["src"]

        return comics_info

    async def search(self, text: str, page: int = 0) -> dict:
        name = "_".join(text.split(" "))
        search_url = f"https://manganato.com/search/story/{name}?page={page + 1}"
        soup = await request(search_url)

        comics = soup.find_all("div", class_="search-story-item")

        if len(comics):
            result_comics: dict = await self.new_comics(comics=comics)
            return result_comics

        else:
            return {}

    @staticmethod
    async def get_comic_images(url: str) -> list[str]:
        soup = await request(url)
        images = soup.find("div", class_="container-chapter-reader").find_all('img')
        raw_images = []
        for image in images:
            raw_images.append(image['src'])
        return raw_images


class Comixextra(BaseWebClass):
    name = "comixextra"
    limit_search: int = 25
    limit_new: int = 30
    get_headers: dict = {
        "Referer": "https://chapmanganato.to/",
    }

    @staticmethod
    def get_chapter_number(url: str) -> float:
        text = url.split("/")[-2]
        chapter = text[text.find("-") + len("-"):]
        try:
            number = float(chapter)
        except ValueError:
            new = chapter.replace("-", ".")
            number = float(new)
        return number

    @staticmethod
    def comic_main_page(soup: BeautifulSoup, data: dict) -> dict:
        chapters = soup.find("tbody", {"id": "list", "offset": "0"}).find_all('td')

        data["all_chapters"].clear()
        for chapter in chapters:
            if chapter.find('a'):
                data["all_chapters"].append(chapter.find('a')['href'] + '/')

        name = soup.find('h1', class_="movie-title mobile-hide").find('span').text.split('\n')
        new_name = [n for n in name[1].split(' ') if n]
        data["name"] = ' '.join(new_name)
        data["rate"] = None
        all_tags = soup.find("div", class_="movie-meta-info").find('dl').find_all('a')
        data['status'] = None
        data["genres"] = [tag.text for tag in all_tags[1:]]
        data["cover_url"] = soup.find("img", {'alt': data['name']})['src']

        return data

    @staticmethod
    async def new_comics(page: int = 0, comics=None) -> dict:
        if comics is None:
            base_url = f"https://comixextra.com/comic-updates/{page + 1}"
            soup = await request(base_url)

            comics = soup.find_all("div", class_="hl-box")

        comics_info: dict = {}

        for comic in comics:
            comic_url = comic.find('a')["href"]
            comics_info[comic_url] = {}
            comics_info[comic_url]["name"] = comic.find('a').text
            try:
                comics_info[comic_url]["cover"] = comic.find("img")["src"]
            except TypeError:
                comics_info[comic_url]["cover"] = None

        return comics_info

    async def search(self, text: str, page: int = 0):
        name = "+".join(text.split(" "))
        search_url = f"https://comixextra.com/search?keyword={name}&page={page + 1}"

        soup = await request(search_url)

        comics = soup.find_all("div", class_="cartoon-box")

        if len(comics):
            result_comics: dict = await self.new_comics(comics=comics)
            return result_comics
        else:
            return {}

    @staticmethod
    async def get_comic_images(url: str) -> list[str]:
        if url.split('/')[-1] != 'full':
            url += 'full'
        soup = await request(url)
        body = soup.find("div", class_="chapter-container").find_all('img')
        images = [part["src"] for part in body]
        return images


sites_list = [  # you must add any class you added here
    Manhwax,
    Chapmanganato,
    Comixextra,
]

valid_sites_dict = {
    the_class.name: the_class for the_class in sites_list
}

__all__ = ('valid_sites', 'valid_sites_dict', 'sites', 'request')
