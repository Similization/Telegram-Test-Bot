import openai
import yaml
from aiogram.dispatcher.filters.state import State, StatesGroup


class ChatGPTState(StatesGroup):
    dialog_state = State()


with open("config.yml", "r") as stream:
    try:
        data: dict = yaml.safe_load(stream)
        openai.api_key = data["openai"]["key"]
    except yaml.YAMLError as exc:
        print(exc)


async def get_chat_gpt_answer(text: str, max_tokens: int = 256, temperature: int = 0):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response["choices"][0]["text"]
