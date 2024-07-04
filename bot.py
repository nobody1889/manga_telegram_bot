from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, CallbackQueryHandler, \
    MessageHandler, filters, InlineQueryHandler

from stuff import valid_sites, add_url, remove_url, show_comics, check
from telegram_bot_properties import *
from telegram_bot_properties.inline_part import my_comics, inline_query_buttons, my_new_chapters, generator

Token = '6968670681:AAEY1wqMF9zGCvsMMty3PXrPGO2wPuAe-ts'
local_keyboard = ['search', 'my comics', 'check for new chapters', "kill"]
ADMIN_USER_ID = 5519596138


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([['search'], ['my comics', 'check for new chapters']], one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_message.chat_id, reply_markup=reply_markup,
                                   text='welcome\n please use </help> if you are new')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
             InlineKeyboardButton("Remove Comics", callback_data='remove_url')],
            [InlineKeyboardButton("My Comics", switch_inline_query_current_chat="my_comics")],
            [InlineKeyboardButton('New Chapters', switch_inline_query_current_chat="my_new_chapters")]

        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Add comics", callback_data='send_url')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data
    print('button')
    match action:
        case 'send_url':
            await query.edit_message_text(text="Please send me the URL.")
            context.user_data["action"] = 'receive_url'
        case 'remove_url':
            await query.edit_message_text(text="Please specify the URL to remove.\n(or all via <all>)")
            context.user_data["action"] = 'remove'
        case 'set_time':
            context.user_data["action"] = 'set_time'


async def handle_url(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    action = context.user_data.get("action")
    print('action: ', action)
    print('text: ', text)
    if action in ['remove', 'receive_url', 'set_time']:
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

            case 'receive_url':
                valued, invalid = await add_url(text, user=str(update.message.from_user.id))
                if valued:
                    await update.message.reply_text(f'LINKs received: \n{valued}')

                if invalid:
                    await update.message.reply_text(f'invalid LINK: \n{invalid}')

                context.user_data["action"] = None

            case 'set_time':
                if await scheduler.set_timer(text, update, context):
                    context.user_data["action"] = None

    elif action in inline_query_buttons:
        print('generator')
        await generator(link=text, action=action, update=update, context=context)
        context.user_data["action"] = None

    elif text.lower() in local_keyboard:
        match text.lower():
            case 'search':
                context.user_data["action"] = None

            case 'my comics':
                await show_main_menu(update, context)

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
    inline_query_handler_my_new_chapters = InlineQueryHandler(callback=my_new_chapters, pattern="my_new_chapters")

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(check_handler)
    button_handler = CallbackQueryHandler(button)
    application.add_handler(button_handler)
    application.add_handlers(handlers=[my_scheduler, CallbackQueryHandler(scheduler.schedule_button)])

    application.add_handler(inline_query_handler_my_comics)
    application.add_handler(inline_query_handler_my_new_chapters)

    application.add_handler(handle_url_handler)

    application.run_polling()
