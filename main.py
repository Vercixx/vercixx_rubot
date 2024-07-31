import asyncio
from logging import basicConfig, debug, info
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

class Memory():
  def __init__(self):
    self.memory = {}
  def add(self, key, value):
    # Also can be used to update the value of a key
    self.memory[key] = value
  def append(self, key, value):
    if isinstance(self.memory[key], list):
      self.memory[key].append(value)
  def get(self, key):
    if self.memory.get(key) is not None:
      return self.memory[key]
    else:
      return None
  def remove(self, key):
    del self.memory[key]

memory = Memory()
app = Flask('')

@dp.business_message(F.text == '!clear')
@dp.message(F.text == '!clear')
async def clear(message: types.Message):
  if memory.get(message.chat.id) is None:
    return await message.reply('No memory to clear')
  memory.remove(message.chat.id)

@dp.business_message(F.text)
@dp.message(F.text)
async def ai(message: types.Message):
  global memory
  if memory.get(message.chat.id) is None:
    memory.add(message.chat.id, [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': message.text}])
  else:
    memory.append(message.chat.id, {'role': 'user', 'content': message.text})
  debug(memory)
  res = ''
  for messages in client.chat_completion(memory.get(message.chat.id), stream=False):
    res += str(messages.choices[0].delta.content)
  await message.answer('💬\n'+res)
  memory.append(message.chat.id, {'role': 'assistant', 'content': res})

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