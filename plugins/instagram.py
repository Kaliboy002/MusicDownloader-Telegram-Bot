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
            "Content-Length": "99",
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
        pattern = r'(https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:p|reel|tv|stories)\/[\w-]+\/?(?:\?[^\s]+)?)'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def determine_content_type(url) -> str:
        content_types = {
            '/p/': 'photo',
            '/reel/': 'reel',
            '/tv': 'igtv',
            '/stories/': 'story',
        }
        for pattern, content_type in content_types.items():
            if pattern in url:
                return content_type
        return 'unknown'

    @staticmethod
    def is_publicly_available(url) -> bool:
        try:
            response = requests.get(url, headers=Insta.headers)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    async def download(client, event):
        link = Insta.extract_url(event.message.text)
        if not link:
            await event.reply("Invalid Instagram link. Please try again.")
            return

        start_message = await event.respond("Processing your Instagram link...")
        content_type = Insta.determine_content_type(link)

        try:
            if content_type in ['photo', 'reel', 'story', 'igtv']:
                await Insta.download_content(client, event, link, content_type)
            else:
                await event.reply("Unsupported content type. Please ensure the link is valid.")
        except Exception as e:
            await event.reply(f"An error occurred: {e}")
        finally:
            await start_message.delete()

    @staticmethod
    async def download_content(client, event, link, content_type):
        try:
            if content_type == 'photo':
                await Insta.download_photo(client, event, link)
            elif content_type == 'reel':
                await Insta.download_reel(client, event, link)
            elif content_type == 'story':
                await Insta.download_story(client, event, link)
            elif content_type == 'igtv':
                await Insta.download_igtv(client, event, link)
            else:
                raise ValueError("Unknown content type.")
        except Exception as e:
            await event.reply(f"Failed to download content: {e}")

    @staticmethod
    async def download_photo(client, event, link):
        try:
            meta_tags = await Insta.search_saveig(link)
            if meta_tags:
                for meta in meta_tags:
                    await asyncio.sleep(1)
                    await Insta.send_file(client, event, meta)
            else:
                raise ValueError("No photos found.")
        except Exception as e:
            await event.reply(f"Error downloading photo: {e}")

    @staticmethod
    async def download_reel(client, event, link):
        try:
            meta_tag = await Insta.get_meta_tag(link, 'og:video')
            if meta_tag:
                content_value = meta_tag['content']
                await Insta.send_file(client, event, content_value)
            else:
                raise ValueError("No reel found.")
        except Exception as e:
            await event.reply(f"Error downloading reel: {e}")

    @staticmethod
    async def download_story(client, event, link):
        try:
            meta_tags = await Insta.search_saveig(link)
            if meta_tags:
                await Insta.send_file(client, event, meta_tags[0])
            else:
                raise ValueError("No stories found.")
        except Exception as e:
            await event.reply(f"Error downloading story: {e}")

    @staticmethod
    async def download_igtv(client, event, link):
        try:
            meta_tag = await Insta.get_meta_tag(link, 'og:video')
            if meta_tag:
                content_value = meta_tag['content']
                await Insta.send_file(client, event, content_value)
            else:
                raise ValueError("No IGTV content found.")
        except Exception as e:
            await event.reply(f"Error downloading IGTV: {e}")

    @staticmethod
    async def get_meta_tag(link, property_name):
        response = requests.get(link).text
        soup = bs4.BeautifulSoup(response, 'html.parser')
        return soup.find('meta', attrs={'property': property_name})

    @staticmethod
    async def search_saveig(link):
        try:
            response = requests.post(
                "https://saveig.app/api/ajaxSearch",
                data={"q": link, "t": "media", "lang": "en"},
                headers=Insta.headers
            )
            if response.ok:
                res = response.json()
                return re.findall(r'href="(https?://[^"]+)"', res['data'])
            return None
        except Exception:
            return None

    @staticmethod
    async def send_file(client, event, content_value):
        try:
            await client.send_file(event.chat_id, content_value, caption="Here's your Instagram content.")
        except:
            file_output = wget.download(content_value)
            await client.send_file(event.chat_id, file_output, caption="Here's your Instagram content.")
