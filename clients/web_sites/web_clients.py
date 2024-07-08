from bs4 import BeautifulSoup
import httpx


async def request(url: str) -> BeautifulSoup:
    client = httpx.AsyncClient()
    res = await client.get(url, timeout=10)

    return BeautifulSoup(res.content, "lxml")


class manhwax:
    limit_search: int = 10
    limit_new: int = 20

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


class chapmanganato:
    limit_search: int = 20
    limit_new: int = 24

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


class comixextra:
    limit_search: int = 25
    limit_new: int = 50

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
        data['status'] = all_tags[0]
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
