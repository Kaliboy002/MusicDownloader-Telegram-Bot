from utils import YoutubeDL, re, lru_cache, hashlib, InputMediaPhotoExternal, db
from utils import os, InputMediaUploadedDocument, DocumentAttributeVideo, fast_upload
from utils import DocumentAttributeAudio, DownloadError, WebpageMediaEmptyError
from run import Button, Buttons


class YoutubeDownloader:

    @classmethod
    def initialize(cls):
        cls.MAXIMUM_DOWNLOAD_SIZE_MB = 1024
        cls.DOWNLOAD_DIR = 'repository/Youtube'

        if not os.path.isdir(cls.DOWNLOAD_DIR):
            os.mkdir(cls.DOWNLOAD_DIR)

    @lru_cache(maxsize=128)
    def get_file_path(url, format_id, extension):
        url = url + format_id + extension
        url_hash = hashlib.blake2b(url.encode()).hexdigest()
        filename = f"{url_hash}.{extension}"
        return os.path.join(YoutubeDownloader.DOWNLOAD_DIR, filename)

    @staticmethod
    def is_youtube_link(url):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]
        for pattern in youtube_patterns:
            match = re.match(pattern, url)
            if match:
                return True
        return False

    @staticmethod
    def extract_youtube_url(text):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]

        for pattern in youtube_patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(2)
                return f'https://www.youtube.com/watch?v={video_id}'

        return None

    @staticmethod
    def _get_formats(url):
        ydl_opts = {
            'listformats': True,
            'no_warnings': True,
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info['formats']
        return formats

    @staticmethod
    async def send_youtube_info(client, event, youtube_link):
        url = youtube_link
        video_id = (youtube_link.split("?si=")[0]
                    .replace("https://www.youtube.com/watch?v=", "")
                    .replace("https://www.youtube.com/shorts/", ""))
        formats = YoutubeDownloader._get_formats(url)

        # Download the video thumbnail
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail_url = info['thumbnail']

        # Filter video and audio formats
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']

        video_buttons = []
        counter = 0
        for f in reversed(video_formats):
            extension = f['ext']
            resolution = f.get('resolution')
            filesize = f.get('filesize') if f.get('filesize') is not None else f.get('filesize_approx')
            if resolution and filesize and counter < 1:  # Only 1 option for video
                filesize = f"{filesize / 1024 / 1024:.2f} MB"
                button_data = f"yt/dl/{video_id}/{extension}/{f['format_id']}/{filesize}"
                button = [Button.inline(f"{extension} - {resolution} - {filesize}", data=button_data)]
                if not button in video_buttons:
                    video_buttons.append(button)
                    counter += 1

        audio_buttons = []
        counter = 0
        for f in reversed(audio_formats):
            extension = f['ext']
            resolution = f.get('resolution')
            filesize = f.get('filesize') if f.get('filesize') is not None else f.get('filesize_approx')
            if resolution and filesize and counter < 1:  # Only 1 option for audio
                filesize = f"{filesize / 1024 / 1024:.2f} MB"
                button_data = f"yt/dl/{video_id}/{extension}/{f['format_id']}/{filesize}"
                button = [Button.inline(f"{extension} - {resolution} - {filesize}", data=button_data)]
                if not button in audio_buttons:
                    audio_buttons.append(button)
                    counter += 1

        buttons = video_buttons + audio_buttons
        buttons.append(Buttons.cancel_button)

        # Set thumbnail attributes
        thumbnail = InputMediaPhotoExternal(thumbnail_url)
        thumbnail.ttl_seconds = 0

        # Send the thumbnail as a picture with format buttons
        try:
            await client.send_file(
                event.chat_id,
               file=thumbnail,
               caption="🇺🇲 Select a format to download it:
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
🇮🇷 :فرمت برای دانلود رو انتخاب کنید ",
               buttons=buttons
               )
        except WebpageMediaEmptyError:
            await event.respond(
               "Select a format to download:",
               buttons=buttons
               )


    @staticmethod
    async def download_and_send_yt_file(client, event):
        user_id = event.sender_id

        if await db.get_file_processing_flag(user_id):
            return await event.respond("🇺🇲 Sorry, another file is being processed ⏳
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
🇮🇷 ببخشید، فایلی قبلاً در حال پردازش⏳")

        data = event.data.decode('utf-8')
        parts = data.split('/')
        if len(parts) == 6:
            extension = parts[3]
            format_id = parts[-2]
            filesize = parts[-1].replace("MB", "")
            video_id = parts[2]

            if float(filesize) > YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB:
                return await event.answer(
                    f"⚠️ The file size is more than {YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB}MB."
                    , alert=True)

            await db.set_file_processing_flag(user_id, is_processing=True)

            local_availability_message = None
            url = "https://www.youtube.com/watch?v=" + video_id

            path = YoutubeDownloader.get_file_path(url, format_id, extension)

            if not os.path.isfile(path):
                downloading_message = await event.respond("Downloading ... wait! ⚡⏳")
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': path,
                    'quiet': True,
                }

                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        duration = info.get('duration', 0)
                        width = info.get('width', 0)
                        height = info.get('height', 0)
                    except DownloadError as e:
                        await db.set_file_processing_flag(user_id, is_processing=False)
                        return await downloading_message.edit(f"Oops, something went wrong! 😬❌:\nError:"
                                                              f"  {str(e).split('Error')[-1]}")
                await downloading_message.delete()
            else:
                local_availability_message = await event.respond(
                    "Downloading ... wait! ⚡⏳")

                ydl_opts = {
                    'format': format_id,
                    'outtmpl': path,
                    'quiet': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        duration = info.get('duration', 0)
                        width = info.get('width', 0)
                        height = info.get('height', 0)
                    except DownloadError as e:
                        await db.set_file_processing_flag(user_id, is_processing=False)

            upload_message = await event.respond("Uploading ... Hold on! 🚀⏳
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
در حال آپلود ... یک لحظه! 🚀⏳")

            try:
                async with client.action(event.chat_id, 'document'):

                    media = await fast_upload(
                        client=client,
                        file_location=path,
                        reply=None,
                        name=path,
                        progress_bar_function=None
                    )

                    if extension == "mp4":
                        uploaded_file = await client.upload_file(media)

                        video_attributes = DocumentAttributeVideo(
                            duration=int(duration),
                            w=int(width),
                            h=int(height),
                            supports_streaming=True,
                        )

                        media = InputMediaUploadedDocument(
                            file=uploaded_file,
                            thumb=None,
                            mime_type='video/mp4',
                            attributes=[video_attributes],
                        )

                    elif extension == "m4a" or extension == "webm":
                        uploaded_file = await client.upload_file(media)

                        audio_attributes = DocumentAttributeAudio(
                            duration=int(duration),
                            title="Downloaded Audio",
                            performer="❤️‍🩹 Downloaded by ➣ @Kddfyu",
                        )

                        media = InputMediaUploadedDocument(
                            file=uploaded_file,
                            thumb=None,
                            mime_type='audio/m4a' if extension == "m4a" else 'audio/webm',
                            attributes=[audio_attributes],
                        )

                    await client.send_file(event.chat_id, file=media,
                                           caption=f"❤️‍🩹 Downloaded by ➣ @Kddfyu  ",
                                           force_document=False,
                                           supports_streaming=True)

                await upload_message.delete()
                await local_availability_message.delete() if local_availability_message else None
                await db.set_file_processing_flag(user_id, is_processing=False)

            except Exception as Err:
                await db.set_file_processing_flag(user_id, is_processing=False)
                return await event.respond(f"Sorry There was a problem with your request.\nReason:{str(Err)}")
        else:
            await event.answer("Invalid button data.")
