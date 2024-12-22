from .glob_variables import BotState
from .buttons import Buttons
from utils import db, TweetCapture
from telethon.errors.rpcerrorlist import MessageNotModifiedError


class BotMessageHandler:
    start_message = """
🇺🇲 **| Welcome to Video Downloader **🎬

📌 You can easily download **Instagram** and **YouTube** videos and reels in high speed and quality⚡

🖇️ **Just simply send me the link or url of that **🙂
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
**🇮🇷 | به ربات دانلودر ویدیو خوش آمدید 🎬**

📌 شما به خیلی آسانی میتوانید ویدیو و فیلم های کوتاه را از** اینستاگرام و یوتیوب **با سرعت و کیفیت بالا دانلود نماید⚡

**🖇️ فقط کافیه لینک ویدیو مورد نظر را به من بفرستید 🙂**
"""

    instruction_message = """
╭┈┈┈┈┈┈┈┈┈┈┈┈┈╮
       🆔🤖 @Kali_Number_BOT 
╰┈┈┈┈┈┈┈┈┈┈┈┈┈╯

╭┈┈┈┈┈┈┈┈┈┈┈┈┈╮
       🆔🤖 @Kali_Number_BOT 
╰┈┈┈┈┈┈┈┈┈┈┈┈┈╯

 ╭┈┈┈┈┈┈┈┈┈┈┈┈┈╮
          🆔🤖: @KaIi_Linux_Bot
 ╰┈┈┈┈┈┈┈┈┈┈┈┈┈╯
        """

    search_result_message = """🎵 The following are the top search results that correspond to your query:
"""

    core_selection_message = """🎵 Choose Your Preferred Download Core 🎵

"""
    JOIN_CHANNEL_MESSAGE = """⚠️ **To use this bot, you must first join our Telegram channels**.
Once you've joined, click on |** Joined** | button to proceed 🔐
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
⚠️** برای استفاده از این ربات، نخست شما باید به کانال‌ های زیر عضو گردید **
پس از پیوستن به کانال روی دکمه | **عضو شدم** | را کلیک نماید 🔐"""

    search_playlist_message = """The playlist contains these songs:"""

    @staticmethod
    async def send_message(event, text, buttons=None):
        chat_id = event.chat_id
        user_id = event.sender_id
        await BotState.initialize_user_state(user_id)
        await BotState.BOT_CLIENT.send_message(chat_id, text, buttons=buttons)

    @staticmethod
    async def edit_message(event, message_text, buttons=None):
        user_id = event.sender_id

        await BotState.initialize_user_state(user_id)
        try:
            await event.edit(message_text, buttons=buttons)
        except MessageNotModifiedError:
            pass

    @staticmethod
    async def edit_quality_setting_message(e):
        music_quality = await db.get_user_music_quality(e.sender_id)
        if music_quality:
            message = (f"Your Quality Setting:\nFormat: {music_quality['format']}\nQuality: {music_quality['quality']}"
                       f"\n\nAvailable Qualities :")
        else:
            message = "No quality settings found."
        await BotMessageHandler.edit_message(e, message, buttons=Buttons.get_quality_setting_buttons(music_quality))

    @staticmethod
    async def edit_core_setting_message(e):
        downloading_core = await db.get_user_downloading_core(e.sender_id)
        if downloading_core:
            message = BotMessageHandler.core_selection_message + f"\nCore: {downloading_core}"
        else:
            message = BotMessageHandler.core_selection_message + "\nNo core setting found."
        await BotMessageHandler.edit_message(e, message, buttons=Buttons.get_core_setting_buttons(downloading_core))

    @staticmethod
    async def edit_subscription_status_message(e):
        is_subscribed = await db.is_user_subscribed(e.sender_id)
        message = f"Subscription settings:\n\nYour Subscription Status: {is_subscribed}"
        await BotMessageHandler.edit_message(e, message,
                                             buttons=Buttons.get_subscription_setting_buttons(is_subscribed))

    @staticmethod
    async def edit_tweet_capture_setting_message(e):
        night_mode = await TweetCapture.get_settings(e.sender_id)
        mode = night_mode['night_mode']
        mode_to_show = "Light"
        match mode:
            case "1":
                mode_to_show = "Dark"
            case "2":
                mode_to_show = "Black"
        message = f"Tweet capture settings:\n\nYour Night Mode: {mode_to_show}"
        await BotMessageHandler.edit_message(e, message, buttons=Buttons.get_tweet_capture_setting_buttons(mode))
