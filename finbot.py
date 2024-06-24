import asyncio
from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch
from telethon.errors.rpcerrorlist import UserNotParticipantError, ChannelPrivateError
from telethon import Button

api_id = '22778502'  # Replace with your Telegram API ID
api_hash = '194944b513a3ec6f5bedd76f3dcd2582'  # Replace with your Telegram API hash
bot_token = '7097762851:AAGgt_jGN7q0H7n5fag-1-f0HHyq9Zm-h-Q'  # Replace with your bot token

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

channel_groups = {
    "m": [-1002077774503, -1001880320793, -1002094875711, -1002078375313,
                  -1002033395453, -1002005934016, -1002098853852, -1001992989527,
                  -1002055667798, -1002031370619, -1002091152179, -1002002926660,
                  -1002068864997]
    # Add more groups if needed
}


@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    help_text = """
**BanBot Commands:**

`/ban [username] [group_name] [delay_in_minutes]`

   - Bans the specified user from all channels in the given group after the specified delay (in minutes).
   - If no delay is provided, the ban is immediate.

`/unban [username] [group_name]`

   - Unbans the specified user from all channels in the given group.

`/stats [group_name]`

   - Shows member details (name, username, joined date) for each channel in the specified group.

**Additional Features:**

- Send a username to the bot in a private message to get a list of buttons for banning them from specific groups.

**Available Group Names:**

{}

**Examples:**

- `/ban @username madeeasy 5`: Bans the user after 5 minutes.
- `/ban @username madeeasy`: Bans the user immediately.
- `/unban @username madeeasy`: Unbans the user.
- `/stats madeeasy`: Shows member stats for the "madeeasy" group.
    """.format("\n".join(f"- {group}" for group in channel_groups.keys()))

    await event.reply(help_text)


@bot.on(events.NewMessage(pattern='/ban'))
async def ban_user(event):
    try:
        parts = event.raw_text.split()
        username = parts[1]
        group_name = parts[2].lower()
        delay = int(parts[3]) if len(parts) > 3 else 0
    except (IndexError, ValueError):
        await event.reply('Invalid command format. Usage: /ban [username] [group_name] [delay_in_minutes]')
        return

    if group_name not in channel_groups:
        await event.reply(f'Invalid group name. Available groups: {", ".join(channel_groups.keys())}')
        return

    await ban_user_in_group(event, group_name, username, delay)


@bot.on(events.NewMessage(pattern='/unban'))
async def unban_user(event):
    args = event.raw_text.split()
    if len(args) != 3:
        await event.reply('Invalid usage. Please provide a user ID/username and a group name.')
        return

    user_to_unban = args[1]
    group_name = args[2].lower()

    if group_name not in channel_groups:
        await event.reply(f'Invalid group name. Available groups: {", ".join(channel_groups.keys())}')
        return

    try:
        user = await bot.get_entity(user_to_unban)
        for channel_id in channel_groups[group_name]:
            channel = await bot.get_entity(channel_id)
            await bot(EditBannedRequest(channel, user, ChatBannedRights(until_date=None, view_messages=None)))
        await event.reply(f'User unbanned successfully from all channels in the "{group_name}" group.')
    except Exception as e:
        await event.reply(f'An error occurred: {str(e)}')


@bot.on(events.NewMessage(pattern='/stats'))
async def channel_stats(event):
    try:
        _, group_name = event.raw_text.split()
    except ValueError:
        await event.reply('Invalid command format. Usage: /stats [group_name]')
        return

    if group_name not in channel_groups:
        await event.reply(f'Invalid group name. Available groups: {", ".join(channel_groups.keys())}')
        return

    stats_message = f"**Stats for {group_name} group:**\n\n"

    for channel_id in channel_groups[group_name]:
        try:
            channel = await bot.get_entity(channel_id)
            participants = await bot(GetParticipantsRequest(
                channel, ChannelParticipantsSearch(''), offset=0, limit=1000, hash=0
            ))

            stats_message += f"**Channel: {channel.title}**\n"
            stats_message += f"Total Members: {participants.count}\n"
            stats_message += "-" * 25 + "\n"

            for participant in participants.participants:
                user = await bot.get_entity(participant.user_id)
                if user and not user.bot:
                    joined_date = participant.date.strftime("%Y-%m-%d") if hasattr(participant, 'date') else "Unknown"
                    stats_message += f"👤 {user.first_name} {user.last_name or ''} (@{user.username or 'N/A'}) | Joined: {joined_date}\n"

            stats_message += "\n" 
        except ChannelPrivateError:
            stats_message += f"Channel {channel_id}: Private\n\n"
            await event.reply(stats_message)
            stats_message = "" 
    
    await event.reply(stats_message)


# ... (rest of the code is the same as before)

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_private_message(event):
    message_text = event.raw_text.strip()
    print("recived private message"+message_text)

    # Check if the message *exactly* matches a known command (e.g., /stats, /help)
    if message_text in ["/stats", "/help", "/ban", "/unban"]: 
        # If it's an exact match, let the other command handlers take care of it
        print("it was a command")
        return

    # If it's not an exact command match, assume it's a username and try to process it
    print("its a user name")
    try:
        user = await bot.get_entity(message_text)
        buttons = []
        for group in channel_groups:
            button = [Button.inline(group, data=f'ban_{group}_{user.id}')]
            buttons.append(button)
        # Send the message with buttons
        await event.reply(f"Select a group to ban {message_text} from:", buttons=buttons)
    except ValueError:
        print(f"[handle_private_message] Invalid user ID/username: {message_text}")
    except Exception as e:
        print(f"[handle_private_message] Unexpected error: {e}")
        await event.reply(f'An unexpected error occurred: {str(e)}')




# Handler for button clicks
@bot.on(events.CallbackQuery(pattern=r'ban_'))
async def ban_button_handler(event):     
    _, group_name, user_id_str = event.data.decode().split("_")
    user_id = int(user_id_str)
    
    print(f"[ban_button_handler] Received ban request for user ID {user_id} in group {group_name}")  # Debugging log

    await ban_user_in_group(event, group_name, user_id) 


async def ban_user_in_group(event, group_name, user_id_or_username, delay=0, reason=None):
    try:
        user = await bot.get_entity(user_id_or_username) # Indentation corrected for lines within the 'try' block
        delay_message = f" in {delay} minutes" if delay > 0 else ""
        response_message = f"User {user.username} will be banned from the {group_name} group{delay_message}."

        initial_message = await event.respond(response_message) 

        if delay > 0:
            await asyncio.sleep(delay * 60)

        for channel_id in channel_groups[group_name]:
            try:
                rights = ChatBannedRights(until_date=None, view_messages=True)
                if reason:
                    rights.comment = reason
                await bot(EditBannedRequest(channel_id, user, rights))
            except UserNotParticipantError:
                pass

        # Edit the original message to confirm the ban
        if isinstance(initial_message, events.Message):
            await initial_message.edit(f"User {user.username} has been banned from the {group_name} group.")
        
    except ValueError as ve:
        print(f"[ban_user_in_group] ValueError: {ve}") # Correct indentation for lines within the 'except ValueError' block
        error_message = "Invalid user ID/username. Please double-check."
        if isinstance(event, events.CallbackQuery):
            await event.answer(error_message, alert=True)
        else:
            await event.reply(error_message)
    except Exception as e:  # Correct indentation - should be at the same level as 'try'
        print(f"[ban_user_in_group] Unexpected error: {e}")
        error_message = f"An error occurred: {str(e)}"
        if isinstance(event, events.CallbackQuery):
            await event.answer(error_message, alert=True)
        else:
            await event.reply(error_message)







if __name__ == '__main__':
    with bot:
        print("Bot is running. Press Ctrl+C to stop.")  # Added this line
        bot.run_until_disconnected()
