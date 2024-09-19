import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from clients.web_sites.web_clients import valid_sites_dict, valid_sites, request
from stuff import search_new, add_url
from stuff import valid_urls


async def check_comics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=update.effective_user.id, text='search for new updates')
        comics = await search_new(str(update.effective_user.id))
        comics_v = [comic for comic in comics.keys() if comics[comic]]

        if comics_v:
            for comic in comics_v:
                text0 = f"new chapters for {comic} :\n"
                text1 = [one for one in comics[comic]]
                text = text0 + '\n'.join(text1)
                await update.message.reply_text(text)
        else:
            await update.message.reply_text('no new chapter')

    except ValueError:
        await update.message.reply_text('no comics added please add one via \n</start>')

    except httpx.ConnectTimeout:
        await update.message.reply_text('please try again')


async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    valid, invalid = valid_urls(url)

    if invalid:
        await context.bot.send_message(chat_id=str(update.effective_user.id), text=f'invalid LINK: \n{invalid}')

    for v in valid:
        url_type = v.split('/')[2].split('.')[0]
        cls = valid_sites_dict[url_type]

        response_content: bytes = await request(url=url, header=cls.get_headers, bfs=True)
        data = cls.comic_main_page(soup=response_content, data={})

        text = f"url: {v}\nname: {data["name"]}\nrate: {data['rate']}\ntags: {data["genres"]}\nchapters: {len(data["all_chapters"])}"
        buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("ADD", callback_data="add_new"),
                        InlineKeyboardButton("DELETE", callback_data="delete"),
                    ]
                ])

        await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=data["cover_url"],
                    caption=text,
                    reply_markup=buttons
                )


async def add_new_comics(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user: int | str):
    valued, invalid = await add_url(text, user=str(user))
    if valued:
        await context.bot.send_message(chat_id=str(update.effective_user.id), text=f'LINKs received: \n{valued}')

    if invalid:
        await context.bot.send_message(chat_id=str(update.effective_user.id), text=f'invalid LINK: \n{invalid}')


__all__ = ('check_comics_command', 'add_new_comics')
