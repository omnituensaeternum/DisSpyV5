import selfcord 
from selfcord.ext import commands
from config import TOKEN, TUSERS, SERVER_ID
import datetime

intents = selfcord.Intents.default()
intents.messages = True
intents.reactions = True
intents.voice_states = True
intents.guilds = True
intents.message_content = True  # Required to access the message content

description = '''A Discord monitoring bot to log user activities.'''

bot = commands.Bot(command_prefix='?', description=description, intents=intents, self_bot=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    guild = selfcord.utils.get(bot.guilds, id=int(SERVER_ID))
    if not guild:
        print(f"Guild with ID {SERVER_ID} not found.")
        return
    
    for user_id in TUSERS:
        category_name = f"Logs for {user_id}"
        category = selfcord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
        
        # Create channels for different events
        await ensure_channel(guild, category, f"{user_id}_message_logs")
        await ensure_channel(guild, category, f"{user_id}_deleted_messages")
        await ensure_channel(guild, category, f"{user_id}_attachments")
        await ensure_channel(guild, category, f"{user_id}_reactions")
        await ensure_channel(guild, category, f"{user_id}_voice_logs")

async def ensure_channel(guild, category, name):
    channel = selfcord.utils.get(category.channels, name=name)
    if not channel:
        await guild.create_text_channel(name, category=category)

@bot.event
async def on_message(message):
    if message.author.id in TUSERS:
        channel_name = f"{message.author.id}_message_logs"
        channel = selfcord.utils.get(message.guild.channels, name=channel_name)
        await channel.send(f"**{message.author.name}**: {message.content}")

@bot.event
async def on_raw_message_delete(payload):
    if payload.cached_message.author.id in TUSERS:
        channel_name = f"{payload.cached_message.author.id}_deleted_messages"
        channel = selfcord.utils.get(payload.cached_message.guild.channels, name=channel_name)
        await channel.send(f"**Deleted message from {payload.cached_message.author.name}**: {payload.cached_message.content}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id in TUSERS:
        channel_name = f"{member.id}_voice_logs"
        channel = selfcord.utils.get(member.guild.channels, name=channel_name)
        if after.channel:
            await channel.send(f"**{member.display_name}** joined voice channel **{after.channel.name}**")
        elif before.channel:
            await channel.send(f"**{member.display_name}** left voice channel **{before.channel.name}**")

bot.run(TOKEN, bot=False)  # Make sure to use the token from your config.py
