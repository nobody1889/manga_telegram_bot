import asyncio
import io
import zipfile

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from stuff import show_comics
from .inline_part import which_site
from clients.web_sites.web_clients import request


def extract_data(data: list) -> dict:
    return {
        "chapters": [int(num) for num in data[-1].split(':')],
        "chapters_type": data[-2],
        "comic_name": data[0]
    }


def get_file(user: str, name: str, chapters: list[int], where: str = "all_chapters") -> list:
    dict_file: dict = show_comics(name=user)
    my_list = []
    for dict_name in dict_file:
        if dict_name["name"] == name:
            if len(chapters) == 2:  # we have range
                for chapter in dict_file[where][chapters[0]:chapters[1]]:
                    my_list.append(chapter)

            else:  # just one chapter is there
                my_list.append(dict_file[where][chapters[-1]])

            return my_list
        else:
            return []


async def image_extractor(cls, chapters: list[str]):  # extract all images
    return cls.get_comic_images(url=chapters)


async def create_cbz_file_from_urls(image_urls) -> io.BytesIO:
    cbz_buffer = io.BytesIO()  # the goal -> do not download anything
    with zipfile.ZipFile(cbz_buffer, "w", zipfile.ZIP_DEFLATED) as cbz_f:
        for num, url in enumerate(image_urls):
            response_content: bytes = await request(url=url, bfs=False)
            image = io.BytesIO(response_content)
            cbz_f.writestr(f'image_{num + 1}.jpg', image.getvalue())
    cbz_buffer.seek(0)
    return cbz_buffer


async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE, string: str):
    data = string.split('-')[1:]
    if len(data) == 2:
        pass

    else:  # len(data) == 3
        data = extract_data(data=data)
        files_list = get_file(
            user=str(update.effective_user.id),
            name=data["comic_name"],
            chapters=data["chapters"],
            # where=data['chapters_type']
        )

        if len(files_list) > 0:
            task = [image_extractor(which_site(file.split('/')[2].split('.')[0]), chapters=file) for file in files_list]
            responses: tuple[list[str]] = await asyncio.gather(*task)

            cbz_buffer = create_cbz_file_from_urls(responses)
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=cbz_buffer,
                filename='comics.cbz')

        else:
            context.bot.send_message(
                chat_id=update.effective_user.id,
                text="No comic found for this name"
            )
