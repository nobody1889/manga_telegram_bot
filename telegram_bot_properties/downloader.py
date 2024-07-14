import asyncio
import io
import zipfile
# import multiprocessing
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import ContextTypes
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
        if dict_file[dict_name]["name"] == name:
            if len(chapters) == 2:  # we have range
                for chapter in dict_file[dict_name][where][chapters[0]:chapters[1]]:
                    my_list.append(chapter)

            else:  # just one chapter is there
                my_list.append(dict_file[dict_name][where][chapters[-1]])

            return my_list
    return []


async def image_extractor(cls, chapters: list[str]) -> list:  # extract all images
    images = await cls.get_comic_images(url=chapters)
    return images


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
    data = string.split('~')[1:]

    if len(data) == 3:
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

            cbz_buffer = await create_cbz_file_from_urls(responses[-1])
            try:
                await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=cbz_buffer,
                    filename='comics.cbz',
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30
                )
            except error.TimedOut:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="if you didn't receive the file please try again"
                )

        else:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="No comic found for this name"
            )
    else:
        raise ValueError("something pass here wrong")


async def get_work_data(update: Update, context: ContextTypes.DEFAULT_TYPE, action, query):
    if action != 'back' and action != "range_download":
        context.user_data["on_work_data"]["range"].append(int(action))
    d_range: list = context.user_data["on_work_data"]["range"]

    if action == 'back' and len(d_range) > 0:
        context.user_data["on_work_data"]["range"].pop()

    if len(d_range) == 2:
        if d_range[0] > d_range[1]:
            d_range[0], d_range[1] = d_range[1], d_range[0]
            context.user_data["on_work_data"]["range"] = d_range

        name = context.user_data["on_work_data"]["name"]
        name_range = ':'.join(str(r) for r in d_range)
        my_download_pattern = f'download~{name}~all_chapters~{name_range}'
        context.user_data["on_work_data"] = None

        await query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"download started . . .[{','.join(str(r) for r in d_range)}]"
        )
        await downloader(update=update, context=context, string=my_download_pattern)

    else:
        await query.edit_message_caption(f"choose the rage of download...[{','.join(str(r) for r in d_range)}]")
        await query.edit_message_reply_markup(context.user_data["on_work_data"]["buttons"])
