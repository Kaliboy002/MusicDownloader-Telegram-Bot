from youtube_dl import YoutubeDL
import hashlib
import os
import re
from telethon import Button
from utils import InputMediaPhotoExternal, db, fast_upload
from run import Buttons
from utils import WebpageMediaEmptyError

class YoutubeDownloader:
    @classmethod
    def initialize(cls):
        cls.MAXIMUM_DOWNLOAD_SIZE_MB = 500  # Set maximum file size for download
        cls.DOWNLOAD_DIR = 'repository/Youtube'
        if not os.path.isdir(cls.DOWNLOAD_DIR):
            os.mkdir(cls.DOWNLOAD_DIR)

    @staticmethod
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
        video_id = youtube_link.split("?v=")[-1].split("&")[0]
        formats = YoutubeDownloader._get_formats(url)

        # Download the video thumbnail
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail_url = info['thumbnail']

        # Filters for video and audio formats
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']

        # Generate buttons for each format with file size
        video_buttons = []
        audio_buttons = []

        # Process audio formats
        for f in reversed(audio_formats):
            extension = f['ext']
            resolution = f.get('resolution')
            filesize = f.get('filesize') if f.get('filesize') else f.get('filesize_approx')
            if filesize:
                filesize = f"{filesize / 1024 / 1024:.2f}MB"
                button_data = f"yt/dl/{video_id}/{extension}/{f['format_id']}/{filesize}"
                button = [Button.inline(f"{extension} - {resolution} - {filesize}", data=button_data)]
                audio_buttons.append(button)

        # Process video formats
        for f in video_formats:
            resolution = f.get('resolution')
            filesize = f.get('filesize') if f.get('filesize') else f.get('filesize_approx')
            if filesize:
                filesize = f"{filesize / 1024 / 1024:.2f}MB"
                button_data = f"yt/dl/{video_id}/mp4/{f['format_id']}/{filesize}"
                button = [Button.inline(f"MP4 - {resolution} - {filesize}", data=button_data)]
                video_buttons.append(button)

        buttons = video_buttons + audio_buttons
        buttons.append(Buttons.cancel_button)

        # Set the thumbnail
        thumbnail = InputMediaPhotoExternal(thumbnail_url)
        thumbnail.ttl_seconds = 0

        # Send the thumbnail with format buttons
        try:
            await client.send_file(
                event.chat_id,
                file=thumbnail,
                caption="Select a format to download:",
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
            return await event.respond("Sorry, There is already a file being processed for you.")

        data = event.data.decode('utf-8')
        parts = data.split('/')
        if len(parts) == 6:
            extension = parts[3]
            format_id = parts[-2]
            filesize = parts[-1].replace("MB", "")
            video_id = parts[2]

            # Check if the file is too large for download
            if float(filesize) > YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB:
                return await event.answer(
                    f"⚠️ The file size is more than {YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB}MB.",
                    alert=True)

            await db.set_file_processing_flag(user_id, is_processing=True)

            url = f"https://www.youtube.com/watch?v={video_id}"
            path = YoutubeDownloader.get_file_path(url, format_id, extension)

            if not os.path.isfile(path):
                downloading_message = await event.respond("Downloading the file for you ...")
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
                    except Exception as e:
                        await db.set_file_processing_flag(user_id, is_processing=False)
                        return await downloading_message.edit(f"Sorry Something went wrong: {str(e)}")

                await downloading_message.delete()
            else:
                local_availability_message = await event.respond(
                    "This file is available locally. Preparing it for you now...")

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
                    except Exception as e:
                        await db.set_file_processing_flag(user_id, is_processing=False)

            upload_message = await event.respond("Uploading ... Please hold on.")

            try:
                async with client.action(event.chat_id, 'document'):
                    media = await fast_upload(
                        client=client,
                        file_location=path,
                        reply=None,
                        name=path,
                    )

                    uploaded_file = await client.upload_file(media)

                    if extension == "mp4":
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
                        audio_attributes = DocumentAttributeAudio(
                            duration=int(duration),
                            title="Downloaded Audio",
                            performer="@Spotify_YT_Downloader_BOT",
                        )

                        media = InputMediaUploadedDocument(
                            file=uploaded_file,
                            thumb=None,
                            mime_type='audio/m4a' if extension == "m4a" else 'audio/webm',
                            attributes=[audio_attributes],
                        )

                    await client.send_file(event.chat_id, file=media,
                                           caption=f"Enjoy!\n@Spotify_YT_Downloader_BOT")

                await upload_message.delete()
                await local_availability_message.delete() if local_availability_message else None
                await db.set_file_processing_flag(user_id, is_processing=False)

            except Exception as Err:
                await db.set_file_processing_flag(user_id, is_processing=False)
                return await event.respond(f"Sorry There was a problem with your request.\nReason:{str(Err)}")
        else:
            await event.answer("Invalid button data.")
