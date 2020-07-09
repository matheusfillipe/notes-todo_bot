from hidden_token import *

import requests
import logging, uuid
import random, string

import github
from github import Github

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import telegram

import sqlitedb as sqdb
from pathlib import Path

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import socketserver
from urllib import parse


STATE_SIZE=12
CLIENT_ID="a12a18e28a4885865798"

awating_users_states=[]
awaiting_users_chatId=[]
tgbot=telegram.Bot(token=tg_token)
gist_filename="tgbot.txt"

DB=sqdb.DB("data.db", "TGBOT", ["chat_id", "access_token", "username", "gist_id"])

class Server(BaseHTTPRequestHandler):
    def _set_response(self, body):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode("utf8"))

    def do_GET(self):
        global awating_users_states
        global awaiting_users_chatId
        global tgbot
        global DB
        body="<center><h1>You can close this page now!</h1></center>"
        self._set_response(body)
        url=self.headers["Referer"]
        params=dict(parse.parse_qsl(parse.urlsplit(url).query))
        if "code" in params and "state" in params and params["state"] in awating_users_states:
            logging.info("Authenticating user with state: "+params["state"])
            index=awating_users_states.index(params["state"])
            chat_id=awaiting_users_chatId[index]
            awating_users_states.pop(index)
            awaiting_users_chatId.pop(index)
            header={"Accept": "application/json"}
            r = requests.post('https://github.com/login/oauth/access_token', data = {'client_id':CLIENT_ID, 'client_secret':client_secret, 'code':params["code"], 'state':params["state"]}, headers=header)
            r=r.json()
            access_token=r["access_token"]
            g = Github(access_token)
            user=g.get_user()
            gist=user.create_gist(public=False, files={gist_filename: github.InputFileContent(content="This is a test line")}, description="Telegram notes bot gist")
            username=str(user.name)
            DB.saveData({"gist_id": gist.id, "username": username, "chat_id": chat_id, "access_token": access_token})            
            tgbot.send_message(chat_id=chat_id, text=f"Welcome {username}. You are authenticated and everything is ready. Type /help to know the commands" )
        else:
            logging.info("Failed to confirm GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

    def do_POST(self):
        pass

class UnixHTTPServer(HTTPServer):
    address_family = socket.AF_UNIX

    def get_request(self):
        request, client_address = super(UnixHTTPServer, self).get_request()
        return (request, ["local", 0])

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name = "tgbot.sock"
        self.server_port = 0

def runServer(server_class=UnixHTTPServer, handler_class=Server, port=8088):
    logging.basicConfig(level=logging.INFO)
    server_address = 'tgbot.sock'#, port)
    try:
      Path(server_address).unlink()
      logging.info("removing "+server_address)
    except:
        pass
    httpd = server_class(server_address, handler_class)
#    httpd = server_class(("127.0.0.1", port), handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

class ghHandler:
    username=None
    chat_id=None
    gist=None
    data=None
    access_token=None

    def __init__(self, chat_id):
        dbId=DB.findExactMath("chat_id", chat_id)
        if len(dbId)==0:
            return
        data=DB.getData(dbId[-1])
        self.data=data
        self.username=data["username"]
        self.access_token=data["access_token"]
        self.chat_id=data["chat_id"]
        g=Github(self.access_token)
        self.gist=g.get_gist(data["gist_id"])
#        print(username["access_token"])

    def readGist(self):
        return self.gist.files[gist_filename].content

    def editGist(self, text):
        self.gist.edit(
            description="Telegram notes bot",
            files={gist_filename: github.InputFileContent(content=text)},
        )


def githelper(update):
    g=ghHandler(update.effective_chat.id)
    return g


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             level=logging.INFO)

logging.info("\nStarting bot!\n\n")

updater = Updater(token=tg_token, use_context=True)
dispatcher = updater.dispatcher

def sendMessage(update, context, message):
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def getArg(update):
    try:
        return "".join(update.message.text.split(" ")[1:])
    except:
        pass


def startgit(update, context):
    g=githelper(update)
    if not g.username is None:
        global awating_users_states
        global awaiting_users_chatId

        code=''.join(random.choices(string.ascii_lowercase + string.digits, k=STATE_SIZE))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Authenticate your github account by oppening this link on your browser and authorizing the app: https://github.com/login/oauth/authorize?scope=read:user%20gist&client_id="+CLIENT_ID+"&state="+code)
        awating_users_states.append(code)
        awaiting_users_chatId.append(update.effective_chat.id)
        logging.info("Awaiting for state: "+code)
    else:
        sendMessage(update, context, "Everything is set up! Don't worry.")
    
def helpFun(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Write your notes and I'll notify you when you log in from another machine.\n\n\n Commands:\n\n/r to read all notes or you can specify a number or a string to search through. e.g.:\n/r 3\n /r eggs\n\n/d to delete certain note specifying the number. e.g.:\n/d 3\n\n\nEVERYTHING you write to me is stored as a new note. Each message is a note.")


def read(update, context):
    g=githelper(update)
    if(g.gist is None):
        start(update, context)
        return
    lines=g.readGist().split("\n")
    read=""
    for i,l in enumerate(lines):
        read+=str(i)+":  "+l+"\n"
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{g.username}'s notes:\n\n{read}")

def delete(update, context):
    g=githelper(update)
    if(g.gist is None):
        start(update, context)
        return
    n=getArg(update)
    if not n:
        sendMessage(update, context, "Please specify a number to Delete")
        return
    lines=g.readGist().split("\n")
    read=""
    try:
        if 0<=int(n)<len(lines):
            for i,l in enumerate(lines):
                if int(n)!=i:
                    read+=l+"\n"            
            g.editGist(read[:-1])
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Deleting {getArg(update)}")
        else:
            sendMessage(update, context, "Please enter with a valid number! check /r")
    except:
        sendMessage(update, context, "Please provide a integer number")

def echo(update, context):
    g=githelper(update)
    if(g.gist is None):
        start(update, context)
        return
    msg=update.message.text
    g.editGist(g.readGist()+"\n"+msg)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Added!")

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command. Try /help")

handler_cmds={
        'start':startgit,
        'help':helpFun,
        'r': read,
        'd': delete, 
        } 


echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

handlers=dict()
for cmd in handler_cmds:
    handlers[cmd] = CommandHandler(cmd, handler_cmds[cmd])
    dispatcher.add_handler(handlers[cmd])

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
runServer()

