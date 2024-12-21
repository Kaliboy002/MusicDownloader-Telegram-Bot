from utils import bs4, wget
from utils import asyncio, re, requests, logging

logging.basicConfig(level=logging.INFO)

class Insta:

    @classmethod
    def initialize(cls):
        cls.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://saveig.app",
            "Connection": "keep-alive",
            "Referer": "https://saveig.app/en",
        }

    @staticmethod
    def is_instagram_url(text) -> bool:
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)(?:\/(?:p|reel|tv|stories)\/(?:[^\s\/]+)|\/([\w-]+)(?:\/(?:[^\s\/]+))?)'
        return bool(re.search(pattern, text))

    @staticmethod
    def extract_url(text) -> str | None:
        pattern = r'(https?:\/\/(?:www\.)?(?:ddinstagram\.com|instagram\.com|instagr\.am)\/(?:p|reel|tv|stories)\/[\w-]+\/?(?:\?[^\s]+)?(?:={1,2})?)'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def determine_content_type(text) -> str:
        content_types = {
            '/p/': 'post',
            '/reel/': 'reel',
            '/tv': 'igtv',
            '/stories/': 'story',
        }
        for pattern, content_type in content_types.items():
            if pattern in text:
                return content_type
        return 'unknown'

    @staticmethod
    def is_publicly_available(url) -> bool:
        try:
            response = requests.get(url, headers=Insta.headers)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error checking availability: {e}")
            return False

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
                await event.reply("Unsupported content type or invalid link.")
            await start_message.delete()
            return True
        except Exception as e:
            logging.error(f"Error downloading content: {e}")
            await event.reply("An error occurred while processing your request.")
            await start_message.delete()
            return False

    @staticmethod
    async def download(client, event) -> bool:
        link = Insta.extract_url(event.message.text)
        if not link:
            await event.reply("No valid Instagram link detected.")
            return False

        start_message = await event.respond("Processing your Instagram link...")
        try:
            if "ddinstagram.com" not in link:
                link = link.replace("instagram.com", "ddinstagram.com")
            return await Insta.download_content(client, event, start_message, link)
        except Exception as e:
            logging.error(f"Fallback error: {e}")
            await Insta.download_content(client, event, start_message, link)

    @staticmethod
    async def download_reel(client, event, link):
        try:
            meta_tag = await Insta.get_meta_tag(link)
            content_value = f"https://ddinstagram.com{meta_tag['content']}" if meta_tag else None
            await Insta.send_file(client, event, content_value)
        except Exception as e:
            logging.error(f"Error downloading reel: {e}")
            await event.reply("Error fetching the reel.")

    @staticmethod
    async def download_post(client, event, link):
        try:
            meta_tags = await Insta.search_saveig(link)
            if meta_tags:
                for i, meta in enumerate(meta_tags):
                    await asyncio.sleep(1)
                    await Insta.send_file(client, event, meta, caption=f"Post part {i + 1}/{len(meta_tags)}")
            else:
                await event.reply("No media found in the post.")
        except Exception as e:
            logging.error(f"Error downloading post: {e}")
            await event.reply("Error fetching the post.")

    @staticmethod
    async def download_story(client, event, link):
        try:
            meta_tags = await Insta.search_saveig(link)
            if meta_tags:
                await Insta.send_file(client, event, meta_tags[0])
            else:
                await event.reply("No media found in the story.")
        except Exception as e:
            logging.error(f"Error downloading story: {e}")
            await event.reply("Error fetching the story.")

    @staticmethod
    async def get_meta_tag(link):
        try:
            response = requests.get(link)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            return soup.find('meta', attrs={'property': 'og:video'})
        except Exception as e:
            logging.error(f"Error fetching meta tag: {e}")
            return None

    @staticmethod
    async def search_saveig(link):
        try:
            response = requests.post(
                "https://saveig.app/api/ajaxSearch",
                data={"q": link, "t": "media", "lang": "en"},
                headers=Insta.headers,
            )
            if response.ok:
                res = response.json()
                return re.findall(r'href="(https?://[^"]+)"', res.get("data", ""))
        except Exception as e:
            logging.error(f"SaveIG API error: {e}")
        return None

    @staticmethod
    async def send_file(client, event, content_value, caption="Here's your Instagram content"):
        try:
            if content_value:
                await client.send_file(event.chat_id, content_value, caption=caption)
            else:
                raise ValueError("Invalid content URL.")
        except Exception as e:
            logging.warning(f"Error sending file: {e}, attempting local download.")
            try:
                fileoutput = wget.download(content_value)
                await client.send_file(event.chat_id, fileoutput, caption=caption)
            except Exception as e:
                logging.error(f"Local download failed: {e}")
                await event.reply("Failed to send the file.")
