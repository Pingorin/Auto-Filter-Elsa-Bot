from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, ChatMemberUpdated
from database.users_chats_db import db
from info import AUTH_CHANNEL
import logging

logger = logging.getLogger(__name__)

# Component 1: Jab user join request bhejta hai
@Client.on_chat_join_request(filters.chat(AUTH_CHANNEL))
async def join_req_handler(client, message: ChatJoinRequest):
    user_id = message.from_user.id
    try:
        if not await db.find_join_req(user_id):
            await db.add_join_req(user_id)
            logger.info(f"User {user_id} added to pending list for chat {message.chat.id}")
    except Exception as e:
        logger.error(f"Error in join_req_handler: {e}")


# Component 2: Database Cleanup (Corrected Logic)
@Client.on_chat_member_updated(filters.chat(AUTH_CHANNEL))
async def member_update_handler(client, message: ChatMemberUpdated):
    try:
        # Yeh check bilkul sahi hai, ise rehne dein
        if not message.new_chat_member:
            return

        user_id = message.new_chat_member.user.id
        
        # Check karein agar user hamari pending list mein tha
        if await db.find_join_req(user_id):
            
            new_status = message.new_chat_member.status
            
            # Agar naya status 'pending' ke alawa kuch bhi hai
            # (matlab approve, decline, ya cancel ho gaya)
            # toh use list se hamesha hata do.
            if new_status in [
                enums.ChatMemberStatus.MEMBER,       # Case: Approved
                enums.ChatMemberStatus.ADMINISTRATOR, # Case: Approved (as admin)
                enums.ChatMemberStatus.OWNER,         # Case: Approved (as owner)
                enums.ChatMemberStatus.RESTRICTED,  # Case: Approved (but restricted)
                enums.ChatMemberStatus.LEFT,        # Case: Declined by admin / Cancelled by user
                enums.ChatMemberStatus.BANNED       # Case: Banned / Declined
            ]:
                await db.remove_join_req(user_id)
                logger.info(f"User {user_id} status updated to {new_status}. Removed from pending list.")

    except AttributeError:
        # Kuch events (jaise title change) mein new_chat_member nahi hota
        pass
    except Exception as e:
        logger.error(f"Error in member_update_handler: {e}")
