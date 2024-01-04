import logging
from aiogram import Bot, Dispatcher, types
import g4f
from aiogram.utils import executor
from md2tgmd import escape
import re
import os

# Включите логирование
logging.basicConfig(level=logging.INFO)

ALLOWED_USERS = [eval(i) for i in os.environ['ALLOWED_USERS'].split(',')] 
# Инициализация бота
API_TOKEN = os.environ['API_TOKEN']
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словарь для хранения истории разговоров
conversation_history = {}

# Функция для обрезки истории разговора
def trim_history(history, max_length=4096):
    current_length = sum(len(message["content"]) for message in history)
    while history and current_length > max_length:
        removed_message = history.pop(0)
        current_length -= len(removed_message["content"])
    return history


@dp.message_handler(commands=['start'])
async def process_clear_command(message: types.Message):
    user_id = message.from_user.id
    await message.reply(escape("Привет! Я маткад ботик. Я глупый, но могу ходить за ответами на твои вопросы в Bing. \nЧтобы начать со мной работать напиши Саше свой UserId –" + '`'+str(user_id)+ '`\nЯ помню только последние 4096 символов нашего диалога, а также не могу дать ответ длиннее 4096 символов.'), parse_mode=types.ParseMode.MARKDOWN_V2)

@dp.message_handler(commands=['clear'])
async def process_clear_command(message: types.Message):
    user_id = message.from_user.id
    conversation_history[user_id] = []
    await message.reply("История диалога очищена.")

# Обработчик для каждого нового сообщения
@dp.message_handler()
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS:
            return await message.reply(escape("У вас нет доступа к маткад ботику."), parse_mode=types.ParseMode.MARKDOWN_V2)

    user_input = message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_input})
    conversation_history[user_id] = trim_history(conversation_history[user_id])

    chat_history = conversation_history[user_id]
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=chat_history,
            provider=g4f.Provider.Bing,
        )
        chat_gpt_response = response
    except Exception as e:
        logging.error(f"{g4f.Provider.Bing.__name__}:", e)
        chat_gpt_response = "Извините, произошла ошибка."

    conversation_history[user_id].append({"role": "assistant", "content": chat_gpt_response})
    print(conversation_history)
    length = sum(len(message["content"]) for message in conversation_history[user_id])
    print(length)
    await message.answer(escape(fix_links(chat_gpt_response[:4095])), parse_mode=types.ParseMode.MARKDOWN_V2)

def fix_links(target_string):
    link_dict = dict(re.findall(r"\[(.+?)\]: (.+?(?= \"\"))", target_string))
    result = re.sub(r"\[(.+?)\]: (.+?(\"\"))", '', target_string, flags=re.M).lstrip()
    links = re.findall(r"\[\^(.+?)\^\]\[.+?\]", result)
    for link in links:
        inline_link =  f' [[{link}]]({link_dict[link]})'
        result = re.sub(r"\[\^({0})\^\]\[{0}\]".format(link), inline_link, result, flags=re.M)

    if link_dict:
        links_block = '\nСсылки:'
        for i in link_dict:
            links_block += f'\n{i}) {link_dict[i]}'

        result += links_block

    return result

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
