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
        pattern = r'(https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:p|reel|tv|stories|[^\s\/]+\/[\w-]+\/?))'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def determine_content_type(url) -> str:
        if "/p/" in url:
            return "post"
        elif "/reel/" in url:
            return "reel"
        elif "/tv/" in url:
            return "igtv"
        elif "/stories/" in url:
            return "story"
        return "unknown"

    @staticmethod
    def is_publicly_available(url) -> bool:
        try:
            response = requests.get(url, headers=Insta.headers)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @staticmethod
    async def download_content(client, event, url) -> bool:
        content_type = Insta.determine_content_type(url)
        try:
            if content_type in ["post", "reel", "igtv", "story"]:
                await Insta.fetch_and_send(client, event, url, content_type)
                return True
            else:
                await event.reply("Invalid or unsupported content type. Please check the link.")
                return False
        except Exception as e:
            logging.error(f"Error in downloading content: {e}")
            await event.reply("Failed to process your request. Please try again later.")
            return False

    @staticmethod
    async def fetch_and_send(client, event, url, content_type):
        try:
            meta_urls = await Insta.search_saveig(url)
            if not meta_urls:
                raise ValueError("No downloadable URLs found.")

            for index, meta_url in enumerate(meta_urls, start=1):
                await asyncio.sleep(1)  # Prevent API rate limits
                caption = f"Downloaded {content_type} {index}/{len(meta_urls)} from Instagram"
                await Insta.send_file(client, event, meta_url, caption)
        except Exception as e:
            logging.error(f"Error fetching media: {e}")
            await event.reply("An error occurred while processing the content.")

    @staticmethod
    async def search_saveig(url):
        try:
            response = requests.post(
                "https://saveig.app/api/ajaxSearch",
                data={"q": url, "t": "media", "lang": "en"},
                headers=Insta.headers
            )
            if response.ok:
                return re.findall(r'href="(https?://[^"]+)"', response.json().get("data", ""))
        except requests.RequestException as e:
            logging.error(f"Error searching SaveIG API: {e}")
        return []

    @staticmethod
    async def send_file(client, event, media_url, caption):
        try:
            await client.send_file(event.chat_id, media_url, caption=caption)
        except Exception as e:
            logging.warning(f"Direct send failed, attempting local download: {e}")
            file_path = wget.download(media_url)
            await client.send_file(event.chat_id, file_path, caption=caption)
