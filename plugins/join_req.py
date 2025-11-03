from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, ChatMemberUpdated
from database.users_chats_db import db
from info import AUTH_CHANNEL
import logging

logger = logging.getLogger(__name__)

# Component 1: Jab user join request bhejta hai (Yeh pehle se sahi hai)
@Client.on_chat_join_request(filters.chat(AUTH_CHANNEL))
async def join_req_handler(client, message: ChatJoinRequest):
    user_id = message.from_user.id
    try:
        if not await db.find_join_req(user_id):
            await db.add_join_req(user_id)
            logger.info(f"User {user_id} added to pending list for chat {message.chat.id}")
    except Exception as e:
        logger.error(f"Error in join_req_handler: {e}")


# Component 2: Database Cleanup (Old aur New Status Dono Check Karega)
@Client.on_chat_member_updated(filters.chat(AUTH_CHANNEL))
async def member_update_handler(client, message: ChatMemberUpdated):
    try:
        # Check karein agar new_chat_member attribute hai
        if not message.new_chat_member:
            return

        user_id = message.new_chat_member.user.id
        
        # Check karein agar user hamari pending list mein tha
        if await db.find_join_req(user_id):
            
            new_status = message.new_chat_member.status
            old_status = message.old_chat_member.status if message.old_chat_member else None

            # --- YEH HAI NAYA LOGIC ---

            # Case 1: Admin ne request Approve ki
            # User 'LEFT' (ya None) se 'MEMBER' ya 'RESTRICTED' bana
            if new_status in [
                enums.ChatMemberStatus.MEMBER,
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.RESTRICTED
            ] and old_status not in [
                enums.ChatMemberStatus.MEMBER,
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.RESTRICTED
            ]:
                await db.remove_join_req(user_id)
                logger.info(f"User {user_id} APPROVED and removed from pending list.")

            # Case 2: Admin ne request Decline/Dismiss ki YA User ne khud Cancel ki
            # User 'LEFT' (ya None) se 'LEFT' hi raha (status change nahi hua)
            # Ya 'BANNED' ho gaya
            elif new_status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                # Yeh check zaroori hai taaki 'Member' ke 'Left' hone par na chale
                if old_status not in [
                    enums.ChatMemberStatus.MEMBER,
                    enums.ChatMemberStatus.ADMINISTRATOR,
                    enums.ChatMemberStatus.OWNER,
                    enums.ChatMemberStatus.RESTRICTED
                ]:
                    await db.remove_join_req(user_id)
                    logger.info(f"User {user_id} DECLINED/CANCELLED and removed from pending list.")

    except AttributeError:
        # Kuch events (jaise title change) mein new_chat_member nahi hota
        pass
    except Exception as e:
        logger.error(f"Error in member_update_handler: {e}")
