import asyncio
from logging import basicConfig, info
from os import environ
from threading import Thread

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from flask import Flask, make_response
from huggingface_hub import InferenceClient
from werkzeug.serving import make_server

basicConfig(level=0)

# if environ['PROXY'] is not None:
#   session = AiohttpSession(proxies=environ['PROXY'])
# else:
session = AiohttpSession()

bot = Bot(environ['TOKEN'], session=session)
client = InferenceClient(model='mistralai/Mistral-Nemo-Instruct-2407', token=environ['HF_TOKEN'])
dp = Dispatcher()

memory = {}
app = Flask('')

@dp.message(F.text == '!clear')
async def clear(message: types.Message):
  if memory.get(message.chat.id) is None:
    return await message.reply('No memory to clear')
  del memory[message.chat.id]

@dp.message(F.text)
async def ai(message: types.Message):
  global memory
  if memory.get(message.chat.id) is None:
    memory[message.chat.id] = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': message.text}]
  else:
    memory[message.chat.id].append({'role': 'user', 'content': message.text})
  msg = await message.answer('⏳')
  res = ''
  for messages in client.chat_completion(memory[message.chat.id], stream=True):
    res += str(messages.choices[0].delta.content)
    await msg.edit_text('💬\n'+res)
  memory[message.chat.id].append({'role': 'assistant', 'content': res})

@app.route('/')
def home():
  return "I'm alive"

async def kill_polling():
  await dp.stop_polling()

@app.route('/stop')
def stop():
  asyncio.run(kill_polling())
  flask_t.shutdown()
  return 'Server has been stopped completely'

def keep_alive():
  flask_t.run()

class ServerThread(Thread):
  def __init__(self, appl):
    Thread.__init__(self)
    self.server = make_server('0.0.0.0', 80, appl)
    self.ctx = appl.app_context()
    self.ctx.push()

  def run(self):
    info('starting server')
    self.server.serve_forever()

  def shutdown(self):
    self.server.shutdown()

async def run():
  t.start()
  await dp.start_polling(bot)

if __name__ == '__main__':
  flask_t = ServerThread(app)
  t = Thread(target=keep_alive)
  asyncio.run(run())