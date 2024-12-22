from utils.database import db
from telethon import events


class BroadcastManager:

    @staticmethod
    async def broadcast_to_sub_members(client, content, content_type="text", button=None):
        """
        Sends a message or media to all users in the broadcast list.

        Args:
            client: The Telegram client instance.
            content: The content to be sent (text, file path, etc.).
            content_type: Type of content ('text', 'photo', 'video', 'document', etc.).
            button: Optional inline buttons.
        """
        user_ids = await db.get_subscribed_user_ids()
        for user_id in user_ids:
            try:
                if content_type == "text":
                    await client.send_message(user_id, content, buttons=button)
                elif content_type in ["photo", "video", "document"]:
                    await client.send_file(user_id, file=content, caption=button)
                else:
                    print(f"Unsupported content type: {content_type}")
            except Exception as e:
                print(f"Failed to send to user {user_id}: {e}")

    @staticmethod
    async def broadcast_to_temp_members(client, content, content_type="text"):
        """
        Sends a message or media to all temporary subscribed users.

        Args:
            client: The Telegram client instance.
            content: The content to be sent (text, file path, etc.).
            content_type: Type of content ('text', 'photo', 'video', 'document', etc.).
        """
        user_ids = await db.get_temporary_subscribed_user_ids()
        for user_id in user_ids:
            try:
                if content_type == "text":
                    await client.send_message(user_id, content)
                elif content_type in ["photo", "video", "document"]:
                    await client.send_file(user_id, file=content)
                else:
                    print(f"Unsupported content type: {content_type}")
            except Exception as e:
                print(f"Failed to send to user {user_id}: {e}")

    @staticmethod
    async def add_sub_user(user_id):
        """
        Adds a user to the broadcast list.
        """
        await db.add_subscribed_user(user_id)

    @staticmethod
    async def remove_sub_user(user_id):
        """
        Removes a user from the broadcast list.
        """
        await db.remove_subscribed_user(user_id)

    @staticmethod
    async def get_all_sub_user_ids():
        """
        Returns all user IDs in the broadcast list.
        """
        return await db.get_subscribed_user_ids()

    @staticmethod
    async def clear_user_ids():
        """
        Clears the broadcast list by removing all user IDs.
        """
        await db.clear_subscribed_users()

    @staticmethod
    async def get_temporary_subscribed_user_ids():
        """
        Returns all user IDs in the temporary broadcast list.
        """
        return await db.get_temporary_subscribed_user_ids()

    @staticmethod
    async def add_all_users_to_temp():
        """
        Adds all users to the temporary broadcast list.
        """
        await db.mark_temporary_subscriptions()

    @staticmethod
    async def remove_all_users_from_temp():
        """
        Removes all users from the temporary broadcast list.
        """
        await db.mark_temporary_unsubscriptions()

    @staticmethod
    async def add_user_to_temp(user_id):
        """
        Adds a user to the temporary broadcast list.
        """
        await db.add_user_to_temp(user_id)


# Example of a broadcasting handler
@client.on(events.CallbackQuery(data=b'broadcast'))
async def handle_broadcast(event):
    try:
        content = "This is a test broadcast message!"  # Replace with your content
        content_type = "text"  # Change based on the content: 'text', 'photo', 'video', 'document'

        # Broadcast to temporary subscribed members
        await BroadcastManager.broadcast_to_temp_members(client, content, content_type)

        await event.reply("Broadcast sent successfully!")
    except Exception as e:
        print(f"Broadcast Failed: {str(e)}")
        await event.reply(f"Broadcast Failed: {str(e)}")
