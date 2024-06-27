import datetime
from updates import reload_check
from telegram import Update
from telegram.ext import ContextTypes


class Scheduler:
    def __init__(self):
        self.__due = None
        self.__name = None

    async def alarm(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        print('alarm')
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

    def remove_job_if_exists(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(self.__name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    async def set_timer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.__name = str(update.effective_message.chat_id)
        try:
            self.__due = datetime.datetime.strptime(context.args[0], '%H:%M').time()
            if self.__due.hour < 0:
                await update.effective_message.reply_text("Sorry we can not go back to future!")
                return

            job_removed = self.remove_job_if_exists(context)
            context.job_queue.run_daily(self.alarm, self.__due, chat_id=self.__name, name=self.__name, data=self.__due)

            text = "Timer successfully set for daily check!"
            if job_removed:
                text += " Old one was removed."
            await update.effective_message.reply_text(text)

        except (IndexError, ValueError):
            await update.effective_message.reply_text("Usage: /set_time <hour>:<minute>")

    async def show_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        pass

    async def unset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        job_removed = self.remove_job_if_exists(context)
        text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
        await update.message.reply_text(text)
