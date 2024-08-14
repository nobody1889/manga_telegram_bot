import os

ADMIN_USER_ID = "<ADMIN ID>"


async def send_files_to_admin(update, context):
    try:
        for user_file in os.listdir('js_holder'):
            if user_file.endswith('.json'):
                await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=f'js_holder/{user_file}',
                    filename=user_file
                )
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="all users files sent to you"
        )
    except FileNotFoundError:
        await context.bot.send_message(
            text="no user found"
        )


def send_errors(func):
    async def wrapper(update, context, *args, **keywords):
        try:
            await func(update, context, *args, **keywords)
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=str(e) + f"\nfor user:\nid:{update.effective_user.id}\nuser name:{update.effective_user.username}",
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="plz use /start"
            )

    return wrapper
