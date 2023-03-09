import logging
import random
from typing import List, Tuple, Optional, Literal

import openai
import yaml
from aiogram import Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from prettytable import PrettyTable

from api.chat_gpt import get_chat_gpt_answer, ChatGPTState
from api.weather import get_weather
from api.yandex.balaboba.balaboba_ import generate_trash
from api.yandex.music.async_client import YAMState
from reprezzent_bot import ReprezzentBot

DATA: dict
YANDEX_DATA: dict
BOT_DATA: dict

with open("config.yml", "r") as stream:
    try:
        DATA = yaml.safe_load(stream)
        BOT_DATA = DATA["telegram"]["bot"]
        YANDEX_DATA = DATA["yandex"]
    except yaml.YAMLError as exc:
        print(exc)

# constants
API_TOKEN = BOT_DATA["token"]
MY_TELEGRAM_ID = BOT_DATA["my_id"]

# tokens for other functions
openai.api_key = DATA["openai"]["key"]
openweather_token = DATA["open_weather"]["key"]

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = ReprezzentBot(token=API_TOKEN)
bot.create_yandex_music_client(token=YANDEX_DATA["music"]["key"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def warning_message(message: types.Message, warning: str):
    await message.reply(text=warning, parse_mode="Markdown")


def create_table(
    column_names: List[str],
    table_data: List[Tuple],
    align: Literal["l", "c", "r"] = "r",
    align_set: Optional[List[str]] = None,
) -> PrettyTable:
    table = PrettyTable(column_names)
    if align_set is None:
        align_set = []
    for i in range(len(column_names)):
        if i < len(align_set):
            table.align[column_names[i]] = align_set[i]
        else:
            table.align[column_names[i]] = align

    for row_data in table_data:
        row_data = list(row_data)
        while len(row_data) < len(column_names):
            row_data.append("<no data>")
        table.add_row(row_data)
    return table


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Hello there! I am reprezzent bot")


@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.reply(
        text="""
Stop, get some help!
    
Reference:
_(arg)_ - required argument
_[arg]_ - not required argument

Commands:
`start` - Start experience
`flip_coin` - Flips coin
`weather` - Show weather in the place where you are
`balaboba` _(text)_ - Use yandex balaboba to generate text
`start_chat_gpt_dialog` - Start ChatGPTState
`stop_chat_gpt_dialog` - Stop ChatGPTState
`cancel` - Cancels any state
`help` - List of available commands
        """,
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["weather"])
async def weather_command(message: types.Message):
    user_id = message.from_id
    if user_id != MY_TELEGRAM_ID:
        await message.reply("This command is not available for you right now")

    arguments_list = message.get_args().split()
    arguments = dict(zip(["city", "country_code"], arguments_list))
    weather_data = get_weather(token=openweather_token, **arguments)

    weather_info = ""
    for weather in weather_data["weather"]:
        weather_info += f'<a href="https://openweathermap.org/img/wn/{weather["icon"]}@2x.png">&#8205;</a>'
        weather_info += f'{str.capitalize(weather["description"])}\n'
    await message.reply(text=weather_info, parse_mode="HTML")

    await message.reply(
        text=f"```\n"
        f"Weather:\n"
        f'\t\t\t\tTemperature: {weather_data["main"]["temp"]}ºC\n'
        f'\t\t\t\tFeels like: {weather_data["main"]["feels_like"]}ºC\n'
        f'\t\t\t\tDiapason: from {weather_data["main"]["temp_min"]}ºC to {weather_data["main"]["temp_max"]}ºC\n'
        f"Wind:\n"
        f'\t\t\t\tSpeed: {weather_data["wind"]["speed"]} meter/sec\n'
        f'\t\t\t\tGust: {weather_data["wind"]["gust"]} meter/sec\n```',
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["flip_coin"])
async def flip_coin_command(message: types.Message):
    await message.reply(f'I guess it is: {random.choice(["eagle", "tails"])}')


@dp.message_handler(commands=["balaboba"])
async def balaboba_command(message: types.Message):
    arguments: str | None = message.get_args()
    if arguments is None or arguments == "":
        await warning_message(
            message=message,
            warning="There is one required argument for this command: _text_\n"
            "Use `/help` command for more information.",
        )
        return
    balaboba_generated_result = await generate_trash(query=arguments)
    # balaboba_generated_result = await function_for_waiting(message, lambda: generate_trash(query=arguments))
    await message.edit_text(f"Generated trash: \n{balaboba_generated_result}")


@dp.message_handler(commands=["start_chat_gpt_dialog"])
async def start_chat_gpt_dialog(message: types.Message):
    await ChatGPTState.dialog_state.set()
    await message.reply(text="ChatGPTState was `activated`", parse_mode="Markdown")


@dp.message_handler(state=ChatGPTState.dialog_state, commands=["stop_chat_gpt_dialog"])
async def stop_chat_gpt_dialog(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply(text="ChatGPTState was `deactivated`", parse_mode="Markdown")


@dp.message_handler(state=ChatGPTState.dialog_state)
async def chat_gpt_dialog(message: types.Message, state: FSMContext):
    async with state.proxy() as state_data:
        state_data["name"] = message.text
    chat_gpt_answer = await get_chat_gpt_answer(text=message.text)
    await message.reply(text=chat_gpt_answer)


@dp.message_handler(commands=["get_yam_playlists"])
async def get_yam_playlists(message: types.Message):
    await YAMState.playlist_list.set()
    user_playlists = bot.yam_client.get_playlists()
    result: List[Tuple] = []
    for playlist in user_playlists:
        result.append(
            (
                playlist.title,
                # f"[{playlist.title}](https://music.yandex.ru/users/{playlist.uid}/playlists/{playlist.kind})",
                playlist.track_count,
            )
        )
    table = create_table(
        column_names=["Playlist name", "Track count"], table_data=result
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("previous", "next")
    await message.reply(
        text="Here is a list of your yandex music playlists:" f"```\n{table}```",
        reply_markup=markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(state="*", commands="cancel")
# @dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"There is no such command: {message.text}")


if __name__ == "__main__":
    # asyncio.run(bot.create_yandex_music_client(token=YANDEX_DATA["music"]["key"]))
    executor.start_polling(dp, skip_updates=True)
    v = "sas"
