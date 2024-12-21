from utils import bs4, wget
from utils import asyncio, re, requests


class Facebook:
    @classmethod
    def initialize(cls):
        cls.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Referer": "https://fbdown.net",
        }

    @staticmethod
    def is_facebook_url(text) -> bool:
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:facebook\.com|fb\.watch)\/[\w\/\?\=\-]+'
        match = re.search(pattern, text)
        return bool(match)

    @staticmethod
    def extract_url(text) -> str | None:
        pattern = r'(https?:\/\/(?:www\.)?(facebook\.com|fb\.watch)\/[\w\/\?\=\-]+)'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def determine_content_type(text) -> str:
        if "fb.watch" in text or "/videos/" in text:
            return "video"
        return None

    @staticmethod
    def is_publicly_available(url) -> bool:
        try:
            response = requests.get(url, headers=Facebook.headers)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    async def download_content(client, event, start_message, link) -> bool:
        content_type = Facebook.determine_content_type(link)
        try:
            if content_type == "video":
                await Facebook.download_video(client, event, link)
                await start_message.delete()
                return True
            else:
                await event.reply(
                    "Sorry, unable to find the requested content. Please ensure it's publicly available."
                )
                await start_message.delete()
                return True
        except Exception as e:
            await event.reply(f"Error: {str(e)}")
            await start_message.delete()
            return False

    @staticmethod
    async def download(client, event) -> bool:
        link = Facebook.extract_url(event.message.text)

        start_message = await event.respond("Processing your Facebook link ....")
        try:
            return await Facebook.download_content(client, event, start_message, link)
        except Exception as e:
            await event.reply(f"Error: {str(e)}")
            await start_message.delete()
            return False

    @staticmethod
    async def download_video(client, event, link):
        try:
            video_url = await Facebook.get_video_url(link)
            if video_url:
                await Facebook.send_file(client, event, video_url)
            else:
                await event.reply("Oops, something went wrong while fetching the video URL.")
        except Exception as e:
            await event.reply(f"Error: {str(e)}")

    @staticmethod
    async def get_video_url(link) -> str | None:
        try:
            post_url = "https://fbdown.net/download.php"
            payload = {"URLz": link}
            response = requests.post(post_url, data=payload, headers=Facebook.headers)

            if response.ok:
                soup = bs4.BeautifulSoup(response.text, "html.parser")
                video_link = soup.find("a", attrs={"href": re.compile(r"https?://.*\.mp4")})
                return video_link["href"] if video_link else None
        except:
            return None

    @staticmethod
    async def send_file(client, event, content_value):
        try:
            await client.send_file(event.chat_id, content_value, caption="Here's your Facebook video")
        except:
            fileoutput = f"{str(content_value)}"
            downfile = wget.download(content_value, out=fileoutput)
            await client.send_file(event.chat_id, fileoutput, caption="Here's your Facebook video")
