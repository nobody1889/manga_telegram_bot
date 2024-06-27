from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, CallbackQueryHandler, \
    MessageHandler, filters

from stuff import valid_sites, add_url, remove_url
from telegram_timer import set_timer, unset, check_comics

Token = '6968670681:AAEY1wqMF9zGCvsMMty3PXrPGO2wPuAe-ts'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # await update.message.reply_text(f'Hi {user.first_name or user.username or user.id}! Welcome to the bot.')
    await show_main_menu(update, context)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    text_part = '\n'.join(valid_sites)
    text = f"""hi {user.first_name} thanks for using our bot first of all :)
you have to use this websites and send me the main page of the comics
please enjoy  :)
{text_part}
"""
    await update.message.reply_text(text)


async def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Send LINK", callback_data='send_url')],
        [InlineKeyboardButton("Remove LINK", callback_data='remove_url')],
        [InlineKeyboardButton("Download", callback_data='download')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'send_url':
        await query.edit_message_text(text="Please send me the URL.")
        context.user_data["action"] = 'reserve_url'
    elif query.data == 'remove_url':
        await query.edit_message_text(text="Please specify the URL to remove.")
        context.user_data["action"] = 'remove'
    elif query.data == 'download':
        await show_download_menu(query, context)
        context.user_data["action"] = 'download'


async def show_download_menu(query, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Get two numbers", callback_data='get_two_numbers')],
        [InlineKeyboardButton("Last Chapter", callback_data='last_chapter')],
        [InlineKeyboardButton("Download All", callback_data='download_all')],
        [InlineKeyboardButton("Limit Size", callback_data='limit_size')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Please choose a download option:", reply_markup=reply_markup)


async def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    action = context.user_data.get("action")

    if context.user_data.get("action") is None:
        await update.message.reply_text("nop i can't understand 😞")
        return

    match action:
        case 'remove':
            valued, invalid = remove_url(url, user=str(update.message.from_user.id))
            if valued == invalid is None:
                await update.message.reply_text("you don't have any link to check")
            else:
                if valued:
                    await update.message.reply_text(f'removed: \n{valued}')
                if invalid:
                    await update.message.reply_text(f'invalid LINK: \n{invalid}')

        case 'reserve_url':
            valued, invalid = add_url(url, user=str(update.message.from_user.id))
            if valued:
                await update.message.reply_text(f'LINKs received: \n{valued}')
            if invalid:
                await update.message.reply_text(f'invalid LINK: \n{invalid}')
                #   disable_web_page_preview=True

        case 'download':
            pass

    context.user_data["action"] = None


async def handle_download_options(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'get_two_numbers':
        await query.edit_message_text(text="Please enter two numbers separated by a space.")
    elif query.data == 'last_chapter':
        await query.edit_message_text(text="Fetching the last chapter...")
    elif query.data == 'download_all':
        await query.edit_message_text(text="Downloading all...")
    elif query.data == 'limit_size':
        await query.edit_message_text(text="Please enter the size limit (or 'None' for no limit).")


if __name__ == '__main__':
    application = ApplicationBuilder().token(Token).build()

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    check_handler = CommandHandler('check', check_comics)
    set_handler = CommandHandler('set_time', set_timer)
    unset_handler = CommandHandler('unset', unset)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(check_handler)
    application.add_handler(set_handler)
    application.add_handler(unset_handler)

    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_download_options))
    application.run_polling()
