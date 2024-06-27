import datetime

from telegram import Update
from telegram.ext import ContextTypes

from stuff import search_new


async def reload_check(name: str):
    return await search_new(name)


async def check_comics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('search for new updates')
    comics = await reload_check(str(update.message.from_user.id))
    if comics:
        for comic in comics:
            text0 = f"new chapter for {comic} :\n"
            text1 = [one for one in comics[comic]]
            text = text0 + '\n'.join(text1)
            await update.message.reply_text(text)
    else:
        await update.message.reply_text('no new chapter')


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"next will be {job.data} hour later!!!(or unset)")
    comics = await reload_check(job.name)
    if comics:
        for comic in comics:
            text0 = f"new chapter for {comic} :\n"
            text1 = [one for one in comics[comic]]
            text = text0 + '\n'.join(text1)
            await context.bot.send_message(job.chat_id, text=text)
    else:
        await context.bot.send_message(job.chat_id, 'no new chapter')


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id

    try:
        due = datetime.datetime.strptime(context.args[0], '%H:%M').time()

        if due.hour < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_daily(alarm, time=due, chat_id=chat_id, name=str(chat_id), data=due)

        text = "Timer successfully set for daily check!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set_time <hour>:<minute>")


async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    pass


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


__all__ = ('set_timer', 'unset', 'check_comics')
