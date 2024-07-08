from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.ext import ContextTypes

from stuff import show_comics, read_new_from_file, valid_sites
from clients.web_sites.web_clients import manhwax, chapmanganato, comixextra

inline_query_buttons = [
    'my_comics',
    'my_new_chapters'
]
sites = [site.split('/')[-2].split('.')[0] for site in valid_sites]

LIMIT_SIZE_OF_ITEMS_QUERY: int = 0


# ACTION: str = ""

async def generator(link, update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    if action == 'my_comics':
        comics = show_comics(name=str(update.effective_user.id))
        comic = comics[link]
        context.user_data["download"] = comic['name']
        await update.message.reply_photo(
            photo=comic["cover_url"],
            caption=f"""
            name: {comic["name"]}\n\nrate: {comic["rate"]}\n\nstatus: {comic["status"]}\n\n tags: {comic["genres"]}
            """,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("first chapter", url=comic["all_chapters"][-1]),
                     InlineKeyboardButton("last chapter", url=comic["all_chapters"][0])],
                    [InlineKeyboardButton("got to download", callback_data="download")]
                ]
            )
        )
    elif action == 'my_new_chapters':
        all_news: dict = read_new_from_file(user=str(update.effective_user.id))
        the_comic: dict = all_news[link]
        new_chapters: list = the_comic["new_chapters"]
        keys = []

        for num, chapter in enumerate(new_chapters):
            text = f'{len(new_chapters) - num}'
            context.user_data.update({"download": [link, the_comic["all_chapters"].index(chapter)]})
            keys.append(
                [
                    InlineKeyboardButton(text=f"read {text}", url=chapter),
                    InlineKeyboardButton(text=f"download {text}", callback_data="download")

                ])

        await update.message.reply_photo(
            photo=the_comic["cover_url"],
            caption=f"""
            name: {the_comic["name"]}
            
            rate: {the_comic["rate"]}
            
            status: {the_comic["status"]}
            
            tags: {the_comic["genres"]}
            
            new chapters
            """,
            reply_markup=InlineKeyboardMarkup(keys)
        )

    elif action == 'search':
        await update.message.reply_text(text='this feature will add soon')

    context.user_data["action"] = None


async def my_comics_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    name = update.effective_user.id
    try:
        context.user_data['action'] = action
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

        await update.inline_query.answer(results, cache_time=0)
    except ValueError:
        await context.bot.send_message(chat_id=name, text='use </start> to add comics')


async def my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await my_comics_inline_query(update, context, 'my_comics')


async def remove_my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await my_comics_inline_query(update, context, 'remove_comics')


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

        await update.inline_query.answer(results, cache_time=0)
    else:
        await context.bot.send_message(chat_id=name, text='nothing to show\nfirst get </check>')


async def search_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, no: bool = True):
    if no:
        buttons = [
            [InlineKeyboardButton(text=site, callback_data=site)
             ] for site in sites]

        await update.message.reply_photo(
            photo="profile.jpg",
            caption='choose one website',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await context.bot.send_message(chat_id=update.effective_user.id, text=context.user_data.get("action"))
    # context.user_data["action"] = None


def which_site(website: str):
    match website:
        case "manhwax":
            return manhwax
        case "chapmanganato":
            return chapmanganato
        case "comixextra":
            return comixextra


async def fetch_search(cls, name: str, limit: int = LIMIT_SIZE_OF_ITEMS_QUERY,
                       offset: int = 0) -> dict:  # cls is the class actually
    searched_data: dict = await cls.search(text=name, page=(offset // limit))
    return searched_data


async def fetch_new(cls, limit: int = LIMIT_SIZE_OF_ITEMS_QUERY, offset: int = 0) -> dict:  # cls is the class actually
    new_data: dict = await cls.new_comics(page=(offset // limit))
    return new_data


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LIMIT_SIZE_OF_ITEMS_QUERY

    website_name = context.user_data.get("action")
    cls = which_site(website_name)()  # class object
    name = update.inline_query.query

    LIMIT_SIZE_OF_ITEMS_QUERY = cls.limit_search

    offset = int(update.inline_query.offset or 0)
    data_batch = await fetch_search(offset=offset, cls=cls, name=name, limit=LIMIT_SIZE_OF_ITEMS_QUERY)

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=data_batch[item]["name"],
            input_message_content=InputTextMessageContent(
                message_text=item,
                disable_web_page_preview=True
            ),
            thumbnail_url=data_batch[item]["cover"]
        ) for item in data_batch
    ]

    next_offset = str(offset + LIMIT_SIZE_OF_ITEMS_QUERY) if len(data_batch) == LIMIT_SIZE_OF_ITEMS_QUERY else ''
    # context.user_data["action"] = "search"
    await update.inline_query.answer(results, cache_time=0, next_offset=next_offset, read_timeout=10)


async def new_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LIMIT_SIZE_OF_ITEMS_QUERY

    website_name = context.user_data.get("action")
    cls = which_site(website_name)  # class object

    LIMIT_SIZE_OF_ITEMS_QUERY = cls.limit_new
    print("LIMIT_SIZE_OF_ITEMS_QUERY : ", LIMIT_SIZE_OF_ITEMS_QUERY)

    offset = int(update.inline_query.offset or 0)
    data_batch = await fetch_new(offset=offset, cls=cls, limit=LIMIT_SIZE_OF_ITEMS_QUERY)

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=data_batch[item]["name"],
            input_message_content=InputTextMessageContent(
                message_text=item,
                disable_web_page_preview=True
            ),
            thumbnail_url=data_batch[item]["cover"]
        ) for item in data_batch
    ]

    next_offset = str(offset + LIMIT_SIZE_OF_ITEMS_QUERY) if len(data_batch) == LIMIT_SIZE_OF_ITEMS_QUERY else ''
    # context.user_data["action"] = "search"
    await update.inline_query.answer(results, cache_time=0, next_offset=next_offset, read_timeout=10)
