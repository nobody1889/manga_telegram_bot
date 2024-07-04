from stuff import search_new
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


class Scheduler:
    def __init__(self):
        self.__due = None
        self.__name: str = ''
        self.time_is_set = False

    async def scheduler_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("set new time", callback_data='set_time')],
        ]
        if self.time_is_set:
            keyboard.extend([
                [InlineKeyboardButton("unset time", callback_data='remove_time')],
                [InlineKeyboardButton("Show scheduled time", callback_data='show_time')]
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.__name = str(update.effective_message.chat_id)
        await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)

    async def schedule_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        response = query.data

        match response:
            case 'set_time':
                context.user_data["action"] = 'set_time'
                await context.bot.send_message(chat_id=self.__name, text='pleas enter the time like '
                                                                         'blow:\n<hour>')
            case 'remove_time':
                await self.unset(update, context)
            case 'show_time':
                await self.show_time(update, context)

    @staticmethod
    async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        await context.bot.send_message(job.chat_id, text=f"next will be {job.data} hour later!!!(or unset)")
        comics = await search_new(job.name)
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

    async def set_timer(self, local_time: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool | None:
        if not self.__name:
            self.__name = str(update.effective_message.chat_id)
        try:
            self.__due = int(local_time) * 60 * 60 * 24

            if self.__due <= 0:
                await context.bot.send_message(chat_id=self.__name, text="Sorry we can't accept the number")
                return

            job_removed = self.remove_job_if_exists(context)

            context.job_queue.run_repeating(self.alarm, self.__due, chat_id=self.__name,
                                            name=self.__name,
                                            data=self.__due)
            self.time_is_set = True

            text = "Timer successfully set for daily check!"
            if job_removed:
                text += " Old one was removed."
            text += "\nplease use /start to continue"
            await update.effective_message.reply_text(text)
            return True
        except (IndexError, ValueError):
            text = 'please type like blow:\n<hour>'
            await update.effective_message.reply_text(text=text)
            return False

    async def show_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self.__due is not None:
            await context.bot.send_message(chat_id=self.__name, text=(str(int(self.__due / (60 * 60 * 24)))) + ' hour')
        else:
            await context.bot.send_message(chat_id=self.__name, text='please set one time')

    async def unset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        job_removed = self.remove_job_if_exists(context)
        self.__due = None
        self.time_is_set = False

        text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
        await context.bot.send_message(chat_id=self.__name, text=text)


__all__ = ('Scheduler',)
