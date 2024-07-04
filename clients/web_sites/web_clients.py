from bs4 import BeautifulSoup


class manhwax:
    url = 'https://manhwax.org'
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

    def new_comics(self, soup: BeautifulSoup):
        comics = [page.find('a')["href"] for page in soup.find_all("div", class_="bs styletere")]
        next_page = soup.find("div", class_="hpage").find_all('a')[-1]['href']

    @staticmethod
    async def search(name: str):
        pass


class mangahentai:
    @staticmethod
    def comic_main_page(soup: BeautifulSoup, data: dict) -> dict:
        chapters = soup.find('div', {"class": "eplister", "id": "chapterlist"}).find('ul').find_all('li')

        data["all_chapters"].clear()
        for chapter in chapters:
            data["all_chapters"].append(chapter.find('a')['href'])

        data["name"] = soup.find('h1').text.split('\n')[-1]
        data["rate"] = float(soup.find("span", class_="score font-meta total_votes").text) * 2
        # all_tags = soup.find("span", class_="mgen").find_all('a')
        # data["genres"] = [tag.text for tag in all_tags]
        data["cover_url"] = soup.find('img', class_="img-responsive")['src']

        return data

    @staticmethod
    def new_comics(soup: BeautifulSoup):
        pass

    @staticmethod
    async def search(name: str):
        pass


class chapmanganato:
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
    def new_comics(soup: BeautifulSoup):
        pass

    @staticmethod
    async def search(name: str):
        pass


class comixextra:
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
    def new_comics(soup: BeautifulSoup):
        pass

    @staticmethod
    async def search(name: str):
        pass
