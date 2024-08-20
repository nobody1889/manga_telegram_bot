from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton, error
from telegram.ext import ContextTypes

from stuff import show_comics, read_new_from_file
from clients.web_sites.web_clients import valid_sites_dict

from admin import send_errors

inline_query_buttons = [
    'my_comics',
    'my_new_chapters'
]

LIMIT_SIZE_OF_ITEMS_QUERY: int = 0


def which_site(website: str):
    try:
        return valid_sites_dict[website]
    except KeyError:
        raise ValueError(f"the key is not valid: {website}")


def button_maker_via_range(the_comic) -> InlineKeyboardMarkup:
    cls = which_site(the_comic["type"])
    out_buttons = []

    for num in range(0, len(the_comic["all_chapters"]), 7):
        in_buttons = []  # Initialize in_buttons inside the outer loop
        for inner_num, comic in enumerate(the_comic["all_chapters"][num:num + 7]):
            res = cls.get_chapter_number(comic)
            in_buttons.append(
                InlineKeyboardButton(
                    text=str(res),
                    callback_data=str(len(the_comic["all_chapters"]) - (inner_num + num))
                )
            )
        out_buttons.append(in_buttons)

    out_buttons.append([InlineKeyboardButton(text="back", callback_data="back")])
    return InlineKeyboardMarkup(out_buttons)


@send_errors
async def generator(update: Update, context: ContextTypes.DEFAULT_TYPE, link):
    action = context.user_data.get("action")
    if action == 'my_comics':
        comics = show_comics(name=str(update.effective_user.id))
        comic = comics[link]

        context.user_data["on_work_data"] = comic
        context.user_data["on_work_data"].update({"buttons": button_maker_via_range(comic)})
        context.user_data["on_work_data"].update({"range": []})

        await update.message.reply_photo(
            photo=comic["cover_url"],
            caption=f"""
            name: {comic["name"]}\n\nrate: {comic["rate"]}\n\nstatus: {comic["status"]}\n\ntags: {comic["genres"]}
            """,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("first chapter", url=comic["all_chapters"][-1]),
                     InlineKeyboardButton("last chapter", url=comic["all_chapters"][0])],
                    [InlineKeyboardButton(
                        # "go to download", callback_data=f"download~{comic['name']}~all_chapters"
                        text="range_download",
                        callback_data="range_download"
                    )]
                ]
            )
        )
        context.user_data["comic_name"] = link
    elif action == 'my_new_chapters':
        all_news: dict = read_new_from_file(user=str(update.effective_user.id))
        the_comic: dict = all_news[link]
        new_chapters: list = the_comic["new_chapters"]
        keys = []

        for num, chapter in enumerate(new_chapters):
            # text = f'{len(new_chapters) - num}'
            cls = which_site(the_comic["type"])
            chap_num = cls.get_chapter_number(chapter)
            keys.append(
                [
                    InlineKeyboardButton(text=f"read {chap_num}", url=chapter),
                    InlineKeyboardButton(
                        text=f"download {chap_num}", callback_data=f"download~{the_comic['name']}~new_chapters~{num}"
                    )

                ])
        keys.append([
            InlineKeyboardButton(
                text="download all",
                callback_data=f"download~{the_comic['name']}~all_chapters~0:{len(the_comic['new_chapters'])}"
            )
        ])

        context.user_data["comic_name"] = link
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

    context.user_data["action"] = None


@send_errors
async def my_comics_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    name = update.effective_user.id
    try:
        context.user_data['action'] = action
        all_comics: dict = show_comics(name=str(name))

        results = []

        if action == 'remove_comics':
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="remove all",
                    input_message_content=InputTextMessageContent(
                        message_text="remove all",
                        disable_web_page_preview=True
                    ),
                    thumbnail_url=None
                ))

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
        await context.bot.send_message(chat_id=name, text='use /start to add comics')


@send_errors
async def my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await my_comics_inline_query(update, context, 'my_comics')
    except error.BadRequest:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='please use /check and try again'
        )


@send_errors
async def remove_my_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await my_comics_inline_query(update, context, 'remove_comics')
    except error.BadRequest:
        await context.bot.send_message(
            text="""
            we are really sorry but you need use /check or inline check first 
            """
        )


@send_errors
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


@send_errors
async def search_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, no: bool = True):
    if no:
        buttons = [
            [InlineKeyboardButton(text=site, callback_data=site)
             ] for site in valid_sites_dict.keys()]

        await update.message.reply_photo(
            photo="profile.jpg",
            caption='choose one website',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await context.bot.send_message(chat_id=update.effective_user.id, text=context.user_data.get("action"))
    # context.user_data["action"] = None


async def fetch_search(cls, name: str, limit: int = LIMIT_SIZE_OF_ITEMS_QUERY,
                       offset: int = 0) -> dict:  # cls is the class actually
    searched_data: dict = await cls.search(text=name, page=(offset // limit))
    return searched_data


async def fetch_new(cls, limit: int = LIMIT_SIZE_OF_ITEMS_QUERY, offset: int = 0) -> dict:  # cls is the class actually
    new_data: dict = await cls.new_comics(page=(offset // limit))
    return new_data


@send_errors
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


@send_errors
async def new_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LIMIT_SIZE_OF_ITEMS_QUERY

    website_name = context.user_data.get("action")
    cls = which_site(website_name)  # class object

    LIMIT_SIZE_OF_ITEMS_QUERY = cls.limit_new

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

    await update.inline_query.answer(results, cache_time=0, next_offset=next_offset, read_timeout=10)
