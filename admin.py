import os


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
