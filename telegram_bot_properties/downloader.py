import asyncio
import io
import zipfile
from telegram import Update, error, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from stuff import show_comics
from .inline_part import which_site
from clients.web_sites.web_clients import request
from admin import send_errors


def extract_data(data: list) -> dict:
    return {
        "chapters": [int(num) for num in data[-1].split(':')],
        "chapters_type": data[-2],
        "comic_name": data[0]
    }


def get_file(user: str, name: str, chapters: list[int], where: str = "all_chapters") -> list:
    dict_file: dict = show_comics(name=user)
    my_list = []

    if len(chapters) == 2 and chapters[0] == chapters[-1]:
        del chapters[1]

    for dict_name in dict_file:
        if dict_file[dict_name]["name"] == name:
            if len(chapters) == 2:  # we have range
                if chapters[0] == 0:
                    for chapter in dict_file[dict_name][where][chapters[0]:chapters[1]]:
                        my_list.append(chapter)
                if chapters[0] - 1 == 0:
                    for chapter in dict_file[dict_name][where][-chapters[1]:]:
                        my_list.append(chapter)
                else:
                    for chapter in dict_file[dict_name][where][-chapters[1]:-(chapters[0] - 1)]:
                        my_list.append(chapter)

            else:  # just one chapter is there
                my_list.append(dict_file[dict_name][where][-chapters[-1]])
            return my_list
    return []


async def image_extractor(cls, chapters: list[str]) -> list:  # extract all images
    images = await cls.get_comic_images(url=chapters)
    return images


async def create_cbz_files_from_urls(image_urls: list, cls) -> io.BytesIO:
    cbz_buffer = io.BytesIO()  # the goal -> do not download anything
    with zipfile.ZipFile(cbz_buffer, "w", zipfile.ZIP_DEFLATED) as cbz_f:
        for num, url in enumerate(image_urls):
            response_content: bytes = await request(url=url, header=cls.get_headers, bfs=False)
            image = io.BytesIO(response_content)
            cbz_f.writestr(f'image_{num + 1}.jpg', image.getvalue())
    cbz_buffer.seek(0)
    return cbz_buffer


@send_errors
async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE, string: str):
    data = string.split('~')[1:]

    if len(data) == 3:
        data = extract_data(data=data)

        files_list = get_file(
            user=str(update.effective_user.id),
            name=data["comic_name"],
            chapters=data["chapters"],
            where=data['chapters_type']
        )

        if len(files_list) > 0:
            cls = which_site(files_list[0].split('/')[2].split('.')[0])
            task = [image_extractor(cls, chapters=file) for file in files_list]
            responses: list[list] = list(await asyncio.gather(*task))
            for number, one_response in enumerate(responses):
                cbz_buffer = await create_cbz_files_from_urls(image_urls=one_response, cls=cls)
                chapter_number = cls.get_chapter_number(files_list[number])
                try:
                    await context.bot.send_document(
                        chat_id=update.effective_user.id,
                        document=cbz_buffer,
                        filename=f'{data["comic_name"]}/chapter:{chapter_number}.cbz',
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
    if action != 'back' and action != "range_download" and action != "left" and action != "right":
        context.user_data["on_work_data"]["range"].append(int(action))
    d_range: list = context.user_data["on_work_data"]["range"]

    if action == 'back' and len(d_range) > 0:
        context.user_data["on_work_data"]["range"].pop()
    elif action == "left" and len(context.user_data["on_work_data"]["buttons"])-1 > context.user_data["on_work_data"]["level"]:
        context.user_data["on_work_data"]["level"] += 1
    elif action == "right" and context.user_data["on_work_data"]["level"] > 0:
        context.user_data["on_work_data"]["level"] -= 1

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
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(context.user_data["on_work_data"]["buttons"][context.user_data["on_work_data"]['level']])
        )
