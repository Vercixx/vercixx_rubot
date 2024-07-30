from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from os import environ
from huggingface_hub import InferenceClient

from flask import Flask
from threading import Thread

from logging import basicConfig

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

@dp.message(F.text)
async def ai(message: types.Message):
  if memory[message.chat.id] is None:
    memory[message.chat.id] = [{'role': 'system', 'content': 'You are a helpful assistant.', 'role': 'user', 'content': message.text}]
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

def keep_alive():
  app.run(host='0.0.0.0', port=80)

async def run():
  t = Thread(target=keep_alive)
  t.start()
  await dp.start_polling(bot)

if __name__ == '__main__':
  import asyncio
  asyncio.run(run())