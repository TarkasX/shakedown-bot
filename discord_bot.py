import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
EVENT_ROLE_ID = int(os.getenv('EVENT_ROLE_ID'))

# Load emojis and events
with open('emojis.json', 'r', encoding='utf-8') as f:
    emojis = json.load(f)

with open('events.json', 'r', encoding='utf-8') as f:
    events = json.load(f)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_current_event():
    # Set timezone to Budapest
    budapest_tz = pytz.timezone('Europe/Budapest')
    current_time = datetime.now(budapest_tz)
    current_day = current_time.strftime('%A')
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_time_value = current_hour * 60 + current_minute

    if current_day in events:
        for event in events[current_day]:
            start_hour, start_minute = map(int, event['start'].split(':'))
            end_hour, end_minute = map(int, event['end'].split(':'))

            start_time_value = start_hour * 60 + start_minute
            end_time_value = end_hour * 60 + end_minute

            if start_time_value <= current_time_value <= end_time_value:
                return event
    return None

async def delete_bot_messages(channel):
    async for message in channel.history(limit=100):
        if message.author == bot.user:
            await message.delete()

async def post_event(channel, event):
    if event:
        emoji = emojis.get(event['emoji'].replace(':', ''), '')
        event_role = f"<@&{EVENT_ROLE_ID}>"
        message = f"Jelenlegi {event_role}:\n\n"
        message += f"{emoji} {event['name']}\n"
        message += f"Ideje: `{event['start']} - {event['end']}`"
        await channel.send(message)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Add timezone info to the connection message
    budapest_tz = pytz.timezone('Europe/Budapest')
    current_time = datetime.now(budapest_tz)
    print(f'Current Budapest time: {current_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')

    channel = bot.get_channel(CHANNEL_ID)

    # Delete previous bot messages
    await delete_bot_messages(channel)

    # Post current event if any
    current_event = get_current_event()
    if current_event:
        await post_event(channel, current_event)

    # Start the event check loop
    check_events.start()

@tasks.loop(minutes=1)
async def check_events():
    channel = bot.get_channel(CHANNEL_ID)
    current_event = get_current_event()

    # Check if there are any bot messages
    bot_messages = []
    async for message in channel.history(limit=100):
        if message.author == bot.user:
            bot_messages.append(message)

    # If there's no current event but there are bot messages, delete them
    if not current_event and bot_messages:
        await delete_bot_messages(channel)

    # If there's a current event but no bot messages, post the event
    elif current_event and not bot_messages:
        await post_event(channel, current_event)

    # If there's a current event and bot messages, check if it's a different event
    elif current_event and bot_messages:
        emoji = emojis.get(current_event['emoji'].replace(':', ''), '')
        new_message = f"Jelenlegi <@&{EVENT_ROLE_ID}>:\n\n"
        new_message += f"{emoji} {current_event['name']}\n"
        new_message += f"Ideje: `{current_event['start']} - {current_event['end']}`"

        if bot_messages[0].content != new_message:
            await delete_bot_messages(channel)
            await post_event(channel, current_event)

bot.run(TOKEN)
