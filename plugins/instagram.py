from utils import bs4, wget
from utils import asyncio, re, requests


class Insta:

    @classmethod
    def initialize(cls):
        cls.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        }

    @staticmethod
    def is_instagram_url(text) -> bool:
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)(?:\/(?:p|reel|tv|stories|p)\/(?:[^\s\/]+))'
        return bool(re.search(pattern, text))

    @staticmethod
    def extract_url(text) -> str | None:
        pattern = r'(https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:p|reel|tv|stories)\/[\w-]+\/?)'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def determine_content_type(text) -> str:
        if '/p/' in text:
            return 'post'
        elif '/reel/' in text:
            return 'reel'
        elif '/tv/' in text:
            return 'igtv'
        elif '/stories/' in text:
            return 'story'
        return None

    @staticmethod
    async def download_content(client, event, start_message, link) -> bool:
        content_type = Insta.determine_content_type(link)
        try:
            if content_type == 'reel':
                await Insta.download_reel(client, event, link)
            elif content_type == 'post':
                await Insta.download_post(client, event, link)
            elif content_type == 'story':
                await Insta.download_story(client, event, link)
            else:
                await event.reply("Sorry, unable to find the requested content. Please ensure it's publicly available.")
            await start_message.delete()
            return True
        except Exception as e:
            await event.reply(f"Error: {e}")
            await start_message.delete()
            return False

    @staticmethod
    async def download(client, event) -> bool:
        link = Insta.extract_url(event.message.text)
        if not link:
            await event.reply("Invalid Instagram URL. Please try again.")
            return False

        start_message = await event.respond("Processing your Instagram link...")
        return await Insta.download_content(client, event, start_message, link)

    @staticmethod
    async def download_reel(client, event, link):
        await Insta.download_media(client, event, link, "reel")

    @staticmethod
    async def download_post(client, event, link):
        await Insta.download_media(client, event, link, "post")

    @staticmethod
    async def download_story(client, event, link):
        await Insta.download_media(client, event, link, "story")

    @staticmethod
    async def download_media(client, event, link, media_type):
        try:
            media_links = Insta.extract_media_links(link)
            if media_links:
                for media_link in media_links:
                    await asyncio.sleep(1)
                    await Insta.send_file(client, event, media_link)
            else:
                await event.reply(f"Unable to retrieve {media_type}. Please ensure the link is public.")
        except Exception as e:
            await event.reply(f"Error downloading {media_type}: {e}")

    @staticmethod
    def extract_media_links(link):
        try:
            response = requests.get(link, headers=Insta.headers)
            if response.ok:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                video_tags = soup.find_all('meta', property='og:video')
                if video_tags:
                    return [tag['content'] for tag in video_tags]
                image_tags = soup.find_all('meta', property='og:image')
                if image_tags:
                    return [tag['content'] for tag in image_tags]
        except Exception as e:
            print(f"Error extracting media links: {e}")
        return None

    @staticmethod
    async def send_file(client, event, content_value):
        try:
            await client.send_file(event.chat_id, content_value, caption="Here's your Instagram content")
        except Exception as e:
            await event.reply(f"Error sending file: {e}")
