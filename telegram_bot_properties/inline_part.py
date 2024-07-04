from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.ext import ContextTypes

from stuff import show_comics, read_new_from_file
from clients.commons import Requests

inline_query_buttons = [
    'my_comics',
    'my_new_chapters',
    'search',

]


async def generator(link, action, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if action == 'my_comics':
        comics = show_comics(name=str(update.effective_user.id))
        comic = comics[link]
        await update.message.reply_photo(
            photo=comic["cover_url"],
            caption=comic["name"],
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("first chapter", url=comic["all_chapters"][-1])],
                    [InlineKeyboardButton("last chapter", url=comic["all_chapters"][0])]
                ]
            )
        )
    elif action == 'my_new_chapters':
        all_news: dict = read_new_from_file(user=str(update.effective_user.id))
        news = all_news[link]["new_chapters"]
        keys = [f"<a href={one}>{num}</a> " for num, one in enumerate(news)]
        await update.message.reply_html(
            text='\n'.join(keys)
        )

    elif action == 'search':
        await update.message.reply_text(text='this feature will add soon')
    # context.user_data["action"] = None


async def my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.id
    try:
        context.user_data['action'] = 'my_comics'
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
        print('local: ', context.user_data['action'])
        await update.inline_query.answer(results)
    except ValueError:
        await context.bot.send_message(chat_id=name, text='use </start> to add comics')


async def my_new_chapters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.id
    all_comics: dict = read_new_from_file(user=str(name))
    context.user_data['action'] = 'my_new_chapters'
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

        print(context.user_data['action'])
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
