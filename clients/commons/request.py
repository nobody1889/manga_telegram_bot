import requests
import asyncio
import httpx


class Requests:
    def sync_req(self, url: str):
        res = requests.get(url)
        return res

    async def __sub_async_req(self, url: str, client):
        return client.get(url)

    async def aget(self, urls: list[str]) -> list:
        client = httpx.Client()
        tasks = [self.__sub_async_req(url, client) for url in urls]
        what_return = list(await asyncio.gather(*tasks))
        return what_return

    # def async_get(self, urls: list[str]) -> list:
    #     responses = list(asyncio.run(self.__aget(urls)))
    #     return responses
