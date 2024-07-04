import httpx
from telegram import Update
from telegram.ext import ContextTypes

from stuff import search_new


async def check_comics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text('search for new updates')
        comics = await search_new(str(update.message.from_user.id))
        if comics:
            for comic in comics:
                text0 = f"new chapters for {comic} :\n"
                text1 = [one for one in comics[comic]]
                text = text0 + '\n'.join(text1)
                await update.message.reply_text(text)
        else:
            await update.message.reply_text('no new chapter')

    except ValueError:
        await update.message.reply_text('no comics added please add one via \n</start>')

    except httpx.ConnectTimeout:
        await update.message.reply_text('please try again')


__all__ = ('check_comics_command',)
