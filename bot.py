from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, CallbackQueryHandler, \
    MessageHandler, filters, InlineQueryHandler

from stuff import valid_sites, remove_url, check
from telegram_bot_properties import *
from telegram_bot_properties.inline_part import my_comics, inline_query_buttons, my_new_chapters, generator, \
    search_buttons, search_query, sites, new_comic, remove_my_comics
from telegram_bot_properties.updates import add_new_comics

Token = '6968670681:AAEY1wqMF9zGCvsMMty3PXrPGO2wPuAe-ts'
local_keyboard = ['search', 'my comics', 'check for new chapters', "kill"]
ADMIN_USER_ID = 5519596138


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = None
    reply_markup = ReplyKeyboardMarkup([['search'], ['my comics', 'check for new chapters']], one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_message.chat_id, reply_markup=reply_markup,
                                   text='welcome\n please use /help if you are new')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["action"] = None
    user = update.message.from_user

    text_part = '\n'.join(valid_sites)
    text = f"""hi {user.first_name} thanks for using our bot first of all :)
you have to use this websites and send me the main page of the comics
please enjoy  :)
{text_part}
"""
    await update.message.reply_text(text)


async def schedule_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scheduler.scheduler_menu(update, context)


async def show_main_menu(update: Update, context: CallbackContext) -> None:
    if check(name=str(update.effective_message.chat_id)):
        keyboard = [
            [InlineKeyboardButton("Add Comics", callback_data='send_url'),
             InlineKeyboardButton("Remove Comics", switch_inline_query_current_chat='remove_comics')],
            [InlineKeyboardButton("My Comics", switch_inline_query_current_chat="my_comics")],
            [InlineKeyboardButton('New Chapters', switch_inline_query_current_chat="my_new_chapters")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Add comics", callback_data='send_url')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose one option:', reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action in sites:
        await update.callback_query.edit_message_caption(
            caption="enjoy"
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text="search", switch_inline_query_current_chat="")],
                    [InlineKeyboardButton(text="add new comic", switch_inline_query_current_chat="new")]
                 ]
            )
        )
        context.user_data["action"] = action
    elif action in ['remove_time', 'set_time', 'show_time']:
        await scheduler.schedule_button(update, context)
    else:
        match action:
            case 'send_url':
                await query.edit_message_text(text="Please send me the URL.")
                context.user_data["action"] = 'receive_url'
            # case 'remove_url':
            #     await query.edit_message_text(text="Please specify the URL to remove.\n(or all via <all>)")
            #     context.user_data["action"] = 'remove'
            case 'download':
                await context.bot.send_message(chat_id=update.effective_user.id, text="this option will add soon")
                print(context.user_data["download"])


async def handle_url(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    action = context.user_data.get("action")

    if action in ['remove_comics', 'receive_url', 'set_time']:
        match action:
            case 'remove_comics':
                valued, invalid = remove_url(text, user=str(update.message.from_user.id))
                if valued == invalid is None:
                    await update.message.reply_text("you don't have any link to check")
                else:
                    if valued:
                        await update.message.reply_text(f'removed: \n{valued}')
                    if invalid:
                        await update.message.reply_text(f'invalid LINK: \n{invalid}')

                context.user_data["action"] = None

            case 'receive_url':
                await add_new_comics(update=update, context=context, text=text)

                context.user_data["action"] = None

            case 'set_time':
                if await scheduler.set_timer(text, update, context):
                    context.user_data["action"] = None

    elif action in inline_query_buttons:
        await generator(link=text, update=update, context=context)

    elif action in sites:
        await add_new_comics(update=update, context=context, text=text)

        context.user_data["action"] = None

    elif text.lower() in local_keyboard:
        match text.lower():
            case 'search':
                await search_buttons(update, context)

            case 'my comics':
                await show_main_menu(update, context)
            case 'check for new chapters':
                await check_comics_command(update, context)
            case 'kill':
                if update.effective_user.id == ADMIN_USER_ID:
                    await update.message.reply_text('you killed the bot 💀')
                    application.stop_running()
                else:
                    await update.message.reply_text("nop i can't understand 😞")

    else:
        await update.message.reply_text("nop i can't understand 😞")


if __name__ == '__main__':
    application = ApplicationBuilder().token(Token).build()
    scheduler = Scheduler()

    start_handler = CommandHandler('start', start_command)
    help_handler = CommandHandler('help', help_command)
    check_handler = CommandHandler('check', check_comics_command)
    my_scheduler = CommandHandler('schedule', schedule_time_command)

    handle_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)

    inline_query_handler_my_comics = InlineQueryHandler(callback=my_comics, pattern='my_comics')
    inline_query_handler_remove_my_comics = InlineQueryHandler(callback=remove_my_comics, pattern='remove_comics')
    inline_query_handler_my_new_chapters = InlineQueryHandler(callback=my_new_chapters, pattern="my_new_chapters")

    inline_query_handler_search_new = InlineQueryHandler(callback=new_comic, pattern='new')
    inline_query_handler_search_name = InlineQueryHandler(callback=search_query, pattern="")

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(check_handler)
    application.add_handler(my_scheduler)

    button_handler = CallbackQueryHandler(button)
    application.add_handler(button_handler)

    application.add_handler(inline_query_handler_my_comics)
    application.add_handler(inline_query_handler_remove_my_comics)
    application.add_handler(inline_query_handler_my_new_chapters)
    application.add_handler(inline_query_handler_search_new)
    application.add_handler(inline_query_handler_search_name)

    application.add_handler(handle_url_handler)

    application.run_polling()
