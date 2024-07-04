from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.ext import ContextTypes

from stuff import show_comics, search_new, read_new_from_file
from clients.commons import Requests


async def generator(text, update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.id
    try:
        all_comics: dict = show_comics(name=str(name))

        results = []

        for comic_name in all_comics:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=all_comics[comic_name]["name"],
                    input_message_content=InputTextMessageContent(
                        message_text=comic_name,
                        disable_web_page_preview=True,
                    ),
                    thumbnail_url=all_comics[comic_name]["cover_url"],
                ))
        context.user_data['action'] = 'my_comics'
        await update.inline_query.answer(results)
    except ValueError:
        await context.bot.send_message(chat_id=name, text='use </start> to add comics')


async def my_new_chapters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.id
    all_comics: dict = read_new_from_file(user=str(name))
    results = []

    if all_comics:
        for comic_name in all_comics:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=all_comics[comic_name]["name"],
                    input_message_content=InputTextMessageContent(
                        message_text=comic_name,
                        disable_web_page_preview=True,
                    ),
                    thumbnail_url=all_comics[comic_name]["cover_url"],
                ))
        context.user_data['action'] = 'my_new_comics'
        await update.inline_query.answer(results)
    else:
        await context.bot.send_message(chat_id=name, text='nothing to show\nfirst get </check>')


async def search(update: Update, context: ContextTypes):
    pass


async def all_new_chapters():
    pass


async def all_popular_chapters():
    pass


async def button_inline():
    pass
