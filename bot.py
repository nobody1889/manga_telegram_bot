from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, CallbackQueryHandler, \
    MessageHandler, filters

import scheduler
from stuff import valid_sites, add_url, remove_url, show_comics
from updates import check_comics
from scheduler import Scheduler

Token = '6968670681:AAEY1wqMF9zGCvsMMty3PXrPGO2wPuAe-ts'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scheduler.scheduler_menu(update, context)


async def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("add comics", callback_data='send_url')],
        [InlineKeyboardButton("Remove comics", callback_data='remove_url')],
        [InlineKeyboardButton("Show My comics", callback_data='show')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data
    match action:
        case 'send_url':
            await query.edit_message_text(text="Please send me the URL.")
            context.user_data["action"] = 'reserve_url'
        case 'remove_url':
            await query.edit_message_text(text="Please specify the URL to remove.")
            context.user_data["action"] = 'remove'
        case 'show':
            await query.edit_message_text(text="Please wait . . .")
            my_comics = show_comics(str(update.effective_message.chat_id))
            await context.bot.send_message(update.effective_message.chat_id, my_comics, disable_web_page_preview=True)


async def handle_url(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    action = context.user_data.get("action")
    print(action)
    if context.user_data.get("action") is None:
        await update.message.reply_text("nop i can't understand 😞")
        return

    match action:
        case 'remove':
            valued, invalid = remove_url(text, user=str(update.message.from_user.id))
            if valued == invalid is None:
                await update.message.reply_text("you don't have any link to check")
            else:
                if valued:
                    await update.message.reply_text(f'removed: \n{valued}')
                if invalid:
                    await update.message.reply_text(f'invalid LINK: \n{invalid}')

            context.user_data["action"] = None

        case 'reserve_url':
            valued, invalid = add_url(text, user=str(update.message.from_user.id))
            if valued:
                await update.message.reply_text(f'LINKs received: \n{valued}')
            if invalid:
                await update.message.reply_text(f'invalid LINK: \n{invalid}')

                context.user_data["action"] = None

        case 'set_time':
            if await scheduler.set_timer(text, update, context):
                context.user_data["action"] = None


if __name__ == '__main__':
    application = ApplicationBuilder().token(Token).build()
    scheduler = Scheduler()
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    check_handler = CommandHandler('check', check_comics)
    my_scheduler = CommandHandler('schedule', schedule_time)

    application.add_handler(help_handler)
    application.add_handler(check_handler)
    application.add_handlers(handlers=[start_handler, CallbackQueryHandler(button)])
    application.add_handlers(handlers=[my_scheduler, CallbackQueryHandler(scheduler.schedule_button)])

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.run_polling()
