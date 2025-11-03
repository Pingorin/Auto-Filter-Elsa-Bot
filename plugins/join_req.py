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


# Component 2: Database Cleanup jab user approve/decline/cancel hota hai
@Client.on_chat_member_updated(filters.chat(AUTH_CHANNEL))
async def member_update_handler(client, message: ChatMemberUpdated):
    try:
        # Check karein agar new_chat_member attribute hai
        if not message.new_chat_member:
            return

        user_id = message.new_chat_member.user.id
        
        # Check karein agar user pending list mein tha
        if await db.find_join_req(user_id):
            
            # Case 1: Admin ne approve kiya
            if message.new_chat_member.status in [
                enums.ChatMemberStatus.MEMBER, 
                enums.ChatMemberStatus.ADMINISTRATOR, 
                enums.ChatMemberStatus.OWNER
            ]:
                await db.remove_join_req(user_id)
                logger.info(f"User {user_id} approved and removed from pending list.")
            
            # Case 2: Admin ne decline kiya YA user ne khud cancel kiya
            # Check karein agar old_chat_member tha (matlab status change hua hai)
            elif message.old_chat_member and message.old_chat_member.status == enums.ChatMemberStatus.MEMBER:
                 if message.new_chat_member.status in [
                    enums.ChatMemberStatus.LEFT, 
                    enums.ChatMemberStatus.BANNED
                ]:
                    await db.remove_join_req(user_id)
                    logger.info(f"User {user_id} request declined/cancelled and removed from pending list.")

    except AttributeError:
        # Kuch ChatMemberUpdated events mein new_chat_member nahi hota (jaise channel title change)
        pass
    except Exception as e:
        logger.error(f"Error in member_update_handler: {e}")
