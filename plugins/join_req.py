from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, ChatMemberUpdated
from database.users_chats_db import db
from info import ADMINS, AUTH_CHANNEL
import asyncio

@Client.on_chat_join_request(filters.chat(AUTH_CHANNEL))
async def join_reqs_handler(client: Client, message: ChatJoinRequest):
    """
    Component 1: Jab user join request bhejta hai,
    use database mein 'pending' list mein add kar do.
    """
    try:
        # Naya function istemaal karein jo user_id aur chat_id dono save karta hai
        await db.add_join_request(message.from_user.id, message.chat.id)
    except Exception as e:
        print(f"Error saving join request: {e}")


@Client.on_chat_member_updated(filters.chat(AUTH_CHANNEL))
async def chat_member_update_handler(client: Client, message: ChatMemberUpdated):
    """
    Component 2: Database cleanup.
    Jab user ka status badle (approve, decline, cancel),
    use 'pending' list se remove kar do.
    """
    user_id = None
    chat_id = message.chat.id

    # <--- FIX: User ID ko new_chat_member (approve) ya old_chat_member (dismiss) se nikalo
    if message.new_chat_member:
        user_id = message.new_chat_member.user.id
    elif message.old_chat_member:
        user_id = message.old_chat_member.user.id
    
    if not user_id:
        # Agar user_id phir bhi na mile, toh event ko ignore karo
        print(f"Could not determine user_id from chat_member_updated event in chat {chat_id}")
        return

    try:
        # Ab user_id mil गया hai.
        # Use pending list se hamesha remove kar do, chaahe approve ho ya dismiss.
        await db.remove_join_request(user_id, chat_id)
    except Exception as e:
        print(f"Error cleaning up join request for user {user_id} in chat {chat_id}: {e}")


@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    """
    Admin command: Pending list ko poori tarah clear karne ke liye.
    """
    # <--- FIX: Changed db.del_join_req() to the new function db.clear_all_join_requests()
    await db.clear_all_join_requests()    
    await message.reply("<b>⚙️ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴘᴇɴᴅɪɴɢ ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ʟᴏɢꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
