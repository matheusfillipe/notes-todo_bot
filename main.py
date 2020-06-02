from telegram.ext import Updater
from . import hidden_token
updater = Updater(token=tg_token, use_context=True)
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             level=logging.INFO)
dispatcher = updater.dispatcher
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Write your notes and I'll notify you when you log in from another machine.\n\n\n Commands:\n\n/r to read all notes or you can specify a number or a string to search through. e.g.:\n/r 3\n /r eggs\n\n/d to delete certain note specifying the number. e.g.:\n/d 3\n\n\nEVERYTHING you write to me is stored as a new note. Each message is a note.")
from telegram.ext import CommandHandler
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', start)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

def read(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Read")
read_handler = CommandHandler('r', read)
dispatcher.add_handler(read_handler)

def delete(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Delete")
delete_handler = CommandHandler('d', delete)
dispatcher.add_handler(delete_handler)

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

updater.start_polling()

from telegram.ext import MessageHandler, Filters
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

#updater.stop()


