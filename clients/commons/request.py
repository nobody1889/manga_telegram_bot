import requests
import asyncio
import httpx


class Requests:
    @staticmethod
    def sync_req(url: str):
        res = requests.get(url)
        return res

    @staticmethod
    async def __sub_async_req(url: str, client):
        return client.get(url)

    async def aget(self, urls: list[str]) -> list:
        client = httpx.Client()
        tasks = [self.__sub_async_req(url, client) for url in urls]
        what_return = list(await asyncio.gather(*tasks))
        return what_return

