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
if YANDEX_DATA["music"]["key"]:
    bot.create_yandex_music_client(token=YANDEX_DATA["music"]["key"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def warning_message(message: types.Message, warning: str):
    # TODO: function should accept arguments and expected arguments count and types
    #  and if something is wrong -> throw warning message
    await message.reply(text=f"_Warning \u26A0_ \n{warning}", parse_mode="Markdown")


def create_markup(data: List[List[str]], *args, **kwargs) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(*args, **kwargs)
    for row_data in data:
        markup.add(*row_data)
    return markup


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


async def create_answer_yam_message(
    message: types.Message,
    text: str,
    image_link: Optional[str] = None,
    markup: Optional[types.ReplyKeyboardMarkup] = None,
    parse_mode: Literal["Markdown", "MarkdownV2", "HTML"] = "Markdown",
):
    if image_link is not None:
        await message.answer_photo(
            photo=image_link, caption=text, reply_markup=markup, parse_mode=parse_mode
        )
    else:
        await message.reply(text=text, reply_markup=markup, parse_mode=parse_mode)


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
`balaboba` \[text] - Use yandex balaboba to generate text
`cancel` - Cancels any state
`flip_coin` - Flips coin
`get_yam_playlists` - Show your YaM playlist
`help` - List of available commands
`start` - Start experience
`start_chat_gpt_dialog` - Start ChatGPT
`stop_chat_gpt_dialog` - Stop ChatGPT
`weather` (city) (country code) - Show weather in the place where you are
        """,
        parse_mode="Markdown",
    )


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, commands=["weather"]
)
async def weather_command(message: types.Message):
    """
    Command to get some weather data from https://openweathermap.org/
    Without arguments, the command will display weather data for the current geolocation.
    With one argument (city) - displays the weather data for the given city.
    The second argument is needed for the exact location of the search (due to the same city names)
    """
    # TODO: function accept arguments like <city name> <country code>
    #  but arguments can be like:
    #  [Saint Petersburg RU], [Moscow RU], [Saint Petersburg]
    #  so need to think about accept of arguments
    weather_data = get_weather(token=openweather_token, **{"city": message.get_args()})
    if weather_data is None:
        await message.reply(
            text=f"No results were found for this query, please check the arguments: {message.get_args()}"
        )

    weather_info = ""
    for weather in weather_data["weather"]:
        weather_info += f'<a href="https://openweathermap.org/img/wn/{weather["icon"]}@2x.png">&#8205;</a>'
        weather_info += f'{str.capitalize(weather["description"])}\n'
    await message.reply(text=weather_info, parse_mode="HTML")

    # TODO: optimize text
    await message.reply(
        text=f"```\n"
        f"Weather:\n"
        f'\t\t\t\tTemperature: {weather_data["main"]["temp"]}ºC\n'
        f'\t\t\t\tFeels like: {weather_data["main"]["feels_like"]}ºC\n'
        f'\t\t\t\tDiapason: from {weather_data["main"]["temp_min"]}ºC to {weather_data["main"]["temp_max"]}ºC\n'
        f"Wind:\n"
        f'\t\t\t\tSpeed: {weather_data["wind"]["speed"]} meter/sec\n'
        f'\t\t\t\tGust: {weather_data["wind"].get("gust", "<no data>")} meter/sec\n```',
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["flip_coin"])
async def flip_coin_command(message: types.Message):
    """
    Command to make choices easier.
    """
    await message.reply(
        text=f'I guess it is: `{random.choice(["eagle", "tails"])}`',
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["balaboba"])
async def balaboba_command(message: types.Message):
    """
    Command to play with Yandex balaboba project,
    which is actually broken.
    """
    arguments: Optional[str] = message.get_args()
    if arguments is None or arguments == "":
        await warning_message(
            message=message,
            warning="There is one required argument for this command: _text_\n"
            "Use /help command for more information.",
        )
        return
    balaboba_generated_result = await generate_trash(query=arguments)
    await message.reply(f"Generated trash: \n{balaboba_generated_result}")


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID,
    commands=["start_chat_gpt_dialog"],
)
async def start_chat_gpt_dialog(message: types.Message):
    """
    Command to activate chatGPT.
    ChatGPT token should be set.
    """
    await ChatGPTState.dialog_state.set()
    await message.reply(text="ChatGPTState was `activated`", parse_mode="Markdown")


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID,
    state=ChatGPTState.dialog_state,
    commands=["stop_chat_gpt_dialog"],
)
async def stop_chat_gpt_dialog(message: types.Message, state: FSMContext):
    """
    Command to deactivate chatGPT.
    ChatGPT token should be set.
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply(text="ChatGPTState was `deactivated`", parse_mode="Markdown")


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, state=ChatGPTState.dialog_state
)
async def chat_gpt_dialog(message: types.Message, state: FSMContext):
    """
    Command to talk with chatGPT.
    ChatGPT token should be set.
    """
    async with state.proxy() as state_data:
        state_data["name"] = message.text
    chat_gpt_answer = await get_chat_gpt_answer(text=message.text)
    await message.reply(text=chat_gpt_answer)


# TODO: fix markup, think about modernization, add [back, <info>, download] buttons logic
@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, commands=["get_yam_playlists"]
)
async def get_yam_playlists_list(message: types.Message):
    """
    Command get playlists from Yandex Music.
    Yandex Music token should be set.
    """
    if bot.yam_client is None:
        return await warning_message(
            message=message, warning="You should set your token"
        )

    await YAMState.playlist_list.set()
    user_playlists = bot.yam_client.get_playlist_list()
    result: List[Tuple] = []
    for playlist in user_playlists:
        result.append((playlist.title, playlist.track_count))
    table = create_table(
        column_names=["Playlist title", "Track count"], table_data=result
    )
    await create_answer_yam_message(
        message=message,
        text="Here is a list of your yandex music playlists:"
        f"```\n{table}```\nPlease enter playlist title, which you want to open",
        markup=create_markup(
            data=[
                [playlist.title for playlist in user_playlists],
                ["previous", "next"],
            ],
            resize_keyboard=True,
            selective=True,
        ),
        parse_mode="MarkdownV2",
    )


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID,
    lambda message: bot.yam_client.get_playlist_by_title(title=message.text) is None,
    state=YAMState.playlist_list,
)
async def get_yam_playlist(message: types.Message):
    return await message.reply(
        text="Bad playlist title. Choose playlist from the keyboard."
    )


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, state=YAMState.playlist_list
)
async def get_yam_playlist(message: types.Message):
    await YAMState.playlist_current.set()

    optional_playlist = bot.yam_client.get_playlist_by_title(title=message.text)
    if optional_playlist is None:
        return await message.reply(
            text="Bad playlist name. Choose playlist from the keyboard."
        )

    track_list = bot.yam_client.get_tracks_from_playlist()
    result: List[Tuple] = []
    for track in track_list:
        result.append(
            (track.title, bot.yam_client.get_artists_name_from_track(track=track))
        )
    table = create_table(column_names=["Track title", "Artists"], table_data=result)

    await create_answer_yam_message(
        message=message,
        text=f"Here is a list of `{optional_playlist.title}` tracks:"
        f"```\n{table}```\nPlease enter track title, which you want to open",
        image_link=optional_playlist.cover.uri,
        markup=create_markup(
            data=[[track.title for track in track_list], ["back", "info", "download"]],
            resize_keyboard=True,
            selective=True,
        ),
        parse_mode="Markdown",
    )


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID,
    lambda message: bot.yam_client.get_track_by_title(title=message.text) is None,
    state=YAMState.playlist_current,
)
async def get_yam_track(message: types.Message):
    return await message.reply(text="Bad track title. Choose track from the keyboard.")


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, state=YAMState.playlist_current
)
async def get_yam_track(message: types.Message):
    await YAMState.track_current.set()

    optional_track = bot.yam_client.get_track_by_title(title=message.text)
    if optional_track is None:
        return await message.reply(
            text="Bad track title. Choose track from the keyboard."
        )

    await create_answer_yam_message(
        message=message,
        text=f"Title: {optional_track.title}\n"
        f"Authors: {bot.yam_client.get_artists_name_from_track(track=optional_track)}\n"
        f"Duration: {optional_track.duration_ms} ms\n"
        f"Track [link](https://music.yandex.ru/track/{optional_track.id})",
        image_link=optional_track.cover_uri.replace("%%", "200x200"),
        markup=create_markup(
            data=[["back", "info", "download"]], resize_keyboard=True, selective=True
        ),
        parse_mode="Markdown",
    )


@dp.message_handler(
    lambda message: message.from_id == MY_TELEGRAM_ID, state="*", commands="cancel"
)
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
    executor.start_polling(dp, skip_updates=True)
