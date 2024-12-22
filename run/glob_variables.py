from utils import os, load_dotenv, dataclass, field, asyncio
from telethon import TelegramClient


@dataclass
class UserState:
    admin_message_to_send: str = None
    admin_broadcast: bool = False
    send_to_specified_flag: bool = False
    search_result: str = None


class BotState:
    channel_usernames = ["Kali_Linux_BOTS"]
    user_states = {}
    lock = asyncio.Lock()

    load_dotenv('config.env')

    BOT_TOKEN = os.getenv('BOT_TOKEN')
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")

    ADMIN_USER_IDS = os.getenv('ADMIN_USER_IDS').split(',')

    if not all([BOT_TOKEN, API_ID, API_HASH, ADMIN_USER_IDS]):
        raise ValueError("Required environment variables are missing.")

    ADMIN_USER_IDS = [int(id) for id in ADMIN_USER_IDS]
    BOT_CLIENT = TelegramClient('bot', int(API_ID), API_HASH)

    @staticmethod
    async def initialize_user_state(user_id):
        if user_id not in BotState.user_states:
            BotState.user_states[user_id] = UserState()

    @staticmethod
    async def get_user_state(user_id):
        async with BotState.lock:
            await BotState.initialize_user_state(user_id)
            return BotState.user_states[user_id]

    @staticmethod
    async def set_user_state(user_id, key, value):
        user_state = await BotState.get_user_state(user_id)
        setattr(user_state, key, value)

    @staticmethod
    async def get_user_state_property(user_id, key):
        user_state = await BotState.get_user_state(user_id)
        return getattr(user_state, key, None)
