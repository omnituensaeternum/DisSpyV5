# DISSPY IS FUCKIN BACK 

# Import necessary libraries
import discord  # Discord library for bot functionality
import json  # To handle JSON files
import time  # To handle time-related functions
import os  # To interact with the operating system
import aiohttp
import sys
from cfg import TOKEN, CSERVER, CLOG, TUSERS, STORAGE_DIR, TERMINATE_KEY, KILL_SWITCH_KEY # Import the bot's token and server ID from a config file


async def setup_bot(client):
    controlLog = client.get_channel(int(CLOG))
    guild = client.get_guild(int(CSERVER))  # Get the guild object using CSERVER ID
    if not guild:
        print("DisSpy account is not in the control server idiot.")
        sys.exit(0)
        return

    # Check for required permissions
    if not guild.me.guild_permissions.manage_channels:
        await controlLog.send("## **[SETUP ERROR]** DisSpy Account does not have permission to manage channels.")
        return

    # Load existing configuration if exists
    data_directory = os.path.join(STORAGE_DIR, 'Data')
    channel_config_path = os.path.join(data_directory, 'channel_ids.json')
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    if os.path.exists(channel_config_path):
        with open(channel_config_path, 'r') as file:
            channel_ids = json.load(file)
    else:
        channel_ids = {}

    # Check and create categories and channels
    for user_id in TUSERS:
        user = client.get_user(int(user_id))
        if not user:
            await controlLog.send(f"## **[SETUP ERROR]** User ID {user_id} not found.")
            continue
        
        user_display_name = user.display_name  # Get user's display name
        category_name = f"{user.display_name} ({user_id})"
        category = None
        # Try to find the category by saved ID first
        if str(user_id) in channel_ids and 'category_id' in channel_ids[str(user_id)]:
            category = guild.get_channel(channel_ids[str(user_id)]['category_id'])

        if not category:
            # Fallback to finding by name if ID lookup fails
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)
                print(f"Created new category for user ID {user_id} with name {category_name}")

        # Update the JSON structure to include category ID
        channel_ids[str(user_id)] = channel_ids.get(str(user_id), {})
        channel_ids[str(user_id)]['category_id'] = category.id  # Store category ID

        channel_names = ['spoken', 'unspoken', 'memories', 'news']  # Names for channels
        channel_ids[str(user_id)] = channel_ids.get(str(user_id), {})
        for channel_name in channel_names:
            if channel_name not in channel_ids[str(user_id)]:
                channel = await category.create_text_channel(channel_name)
                channel_ids[str(user_id)][channel_name] = channel.id
                print(f"Created new channel {channel_name} under category {category_name}")
                time.sleep(1)
            else:
                print(f"Channel {channel_name} already exists under category {category_name}") # we dont need this yappin in the discord log
        time.sleep(2)

    # Save updated channel IDs to file
    with open(channel_config_path, 'w') as file:
        json.dump(channel_ids, file)
    await controlLog.send("**[Setup] Channel setup saved successfully! Setup is complete.**")
    time.sleep(2)


class MessageDeleterClient(discord.Client):
    async def on_ready(self):
        controlLog = client.get_channel(int(CLOG))
        print("Logged in as", self.user)
        timestamp = f"<t:{int(time.time())}:F>"
        await controlLog.send(f"**Logged in as ``{self.user}`` at {timestamp}**")
        await controlLog.send(f"** Starting Setup Proccess monitor for errors...**")
        await setup_bot(self)  # Setup the bots channels ensuring the bot is in the control server
        await controlLog.send(f"## [DisSpy is now online]")
        await controlLog.send(f"## Tracking ``{len(TUSERS)}`` user(s) in ``{len(self.guilds)}`` server(s)...")
        await controlLog.send(f"## -------------[Tracked Users]------------- \n")
        for u in TUSERS:
            #print each users display name, name, and id
            await controlLog.send("## ------------------------------------------------\n")
            await controlLog.send(f"**Display name:** ``{self.get_user(int(u)).display_name}``")
            await controlLog.send(f"**Username:** ``{self.get_user(int(u)).name}``")
            await controlLog.send(f"**User ID:** ``{u}``")
            await controlLog.send(f"**User Avatar:** {self.get_user(int(u)).display_avatar.url}")
            await controlLog.send(f"**User created at**: ``{self.get_user(int(u)).created_at}``")
            time.sleep(3)
            #we want to log user statuses bio status and game activity either here or perodically elesewhere eventually
        await controlLog.send("## ------------------------------------------------\n https://tenor.com/view/monkey-toy-story3-gif-25030026")
    
    async def get_channel_for_user(self, user_id, channel_name):
        controlLog = client.get_channel(int(CLOG)) #logger for the discord server 
        # Load channel configurations
        data_directory = os.path.join(STORAGE_DIR, 'Data')
        channel_config_path = os.path.join(data_directory, 'channel_ids.json')
        with open(channel_config_path, 'r') as file:
            channel_ids = json.load(file)
        # Get the channel ID from the configuration
        channel_id = channel_ids.get(str(user_id), {}).get(channel_name)
        if channel_id:
            return channel_id
        else:
            await controlLog.send(f"Channel fetching error No channel ID found for user {user_id} and channel {channel_name}") #this only happens when channel_ids is fucked tbh
            return None
    #working
    async def on_message_delete(self, message):
        if str(message.author.id) in TUSERS:
            timestamp = f"<t:{int(time.time())}:F>"
            print(f"Deleted message by {message.author.name}: {message.content} at {timestamp}")
            channel = client.get_channel(await self.get_channel_for_user(message.author.id, 'unspoken'))
            if channel:
                if message.attachments:
                    await channel.send(f"**[Deleted message Event]** [**``{message.author.display_name}``**|**``{message.author.name}``**]** at {timestamp} in **(**{message.guild.name}**)-[**{message.channel.name}**]:** '``Attachment:``'**")
                    for attachment in message.attachments:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status != 200:
                                    return await channel.send('Could not download deleted attachment...')
                                data = await resp.read()
                                with open(attachment.filename, 'wb') as f:
                                    f.write(data)
                        await channel.send(file=discord.File(attachment.filename))
                    os.remove(attachment.filename)
                else:    
                    await channel.send(f"**[Deleted message Event]** [**``{message.author.display_name}``**|**``{message.author.name}``**]** at {timestamp} in **(**{message.guild.name}**)-[**{message.channel.name}**]:** '``{message.content}``'**")
    #working
    async def on_message_edit(self, before, after):
        if str(before.author.id) in TUSERS:
            timestamp = f"<t:{int(time.time())}:F>"
            print(f"Edited message by {before.author.name} from '{before.content}' to '{after.content}' at {timestamp}")
            channel = client.get_channel(await self.get_channel_for_user(before.author.id, 'unspoken'))
            if channel:
                await channel.send(f"**[Edited Message Event]**  [**``{before.author.display_name}``**|**``{before.author.name}``**]** at {timestamp} in **(**{before.guild.name}**)-[**{before.channel.name}**]:** **'``{before.content}``**' --> '``{after.content}``' link:** {after.jump_url}")
    #works great
    async def on_user_update(self, before, after):
        # print(f"detected user update: {before} to {after}") # this is a lot of data
        if str(after.id) in TUSERS:
            timestamp = f"<t:{int(time.time())}:F>"
            channel = client.get_channel(await self.get_channel_for_user(after.id, 'news'))
            if channel:
                await channel.send(f"## [User Update Event for ``{before.name}`` at {timestamp}]")
                if before.name != after.name:
                    await channel.send(f"**[Name updated]** ``{before.name}`` **-->** ``{after.name}``")
                if before.display_avatar.url != after.display_avatar.url:
                    await channel.send(f"**[Avatar updated]**\n **Before: ** {before.display_avatar.url} \n **After: **{after.display_avatar.url}")
                if before.display_name != after.display_name:
                    await channel.send(f"**[Nickname Updated]** ``{before.display_name}`` **-->** ``{after.display_name}``")
    #working accept voice messages untested                
    async def on_message(self, message):
        controlLog = client.get_channel(int(CLOG))
        timestamp = f"<t:{int(time.time())}:F>"
        # print(f"Message by {message.author.name}: {message.content} at {timestamp} in {message.guild.name} - {message.channel.name}\n")
        if message.guild is None: # Ignore DMs
            return
        if str(message.author.id)  in TUSERS:
            timestamp = f"<t:{int(time.time())}:F>"
            channel = client.get_channel(await self.get_channel_for_user(message.author.id, 'spoken'))
            if channel:
                await channel.send(f"**[**``{message.author.display_name}``**|**``{message.author.name}``**]** at {timestamp} in **(**{message.guild.name}**)-[**{message.channel.name}**]:** ``{message.content}`` | **link:** {message.jump_url}")
            if message.attachments is not None:
                att_channel = client.get_channel(await self.get_channel_for_user(message.author.id, 'memories'))
                if att_channel:
                    for attachment in message.attachments:
                        if attachment.is_voice_message():
                            await att_channel.send(f"Voice message: {attachment.url}")
                        await att_channel.send(f"Attachment: {attachment.url}")
                else:
                    await controlLog.send(f"## [Attachment Error] No attachment channel found for user {message.author.name} ({message.author.id})")


        # # Check for termination keyword
        if TERMINATE_KEY and TERMINATE_KEY.lower() in message.content.lower():
            await controlLog.send(f"**Termination keyword detected.**\n Sent by {message.author.name}\n **Shutting down at** {timestamp}**...**")
            print("Termination keyword detected. Shutting down...")
            await self.close()
            sys.exit(0)  # Ensure the program is fully terminated
            
        #clean our data and run for the hills
        if KILL_SWITCH_KEY and KILL_SWITCH_KEY.lower() in message.content.lower():
            await controlLog.send(f"**Killswitch keyword detected.**\n Sent by {message.author.name}\n **Wiping data at** {timestamp}**...**")
            print("Killswitch keyword detected. Wiping data...")
            guild = client.get_guild(int(CSERVER))
            if guild:
                for channel in guild.text_channels:
                    await channel.delete()
                    time.sleep(1)
                for category in guild.categories:
                    time.sleep(1)
                    await category.delete()
            await self.close()
            sys.exit(0)
            
client = MessageDeleterClient()
client.run(TOKEN)  # Use the bot token to log in



  #Unimplemented functions to be worked on later
    #                
    #reactions are weird ill figure this shit out later
    # async def on_raw_reaction_add(self, reaction, user):
    #     if str(user.id) in TUSERS:
    #         timestamp = f"<t:{int(time.time())}:F>"
    #         print(f"Reaction added by {user.name} to message {reaction.message.content} - {reaction.emoji} at {timestamp}")
    #         channel = client.get_channel(await self.get_channel_for_user(user.id, 'spoken'))
    #         if channel:
    #             await channel.send(f"Reaction added by {user.name} to message {reaction.message.content} - {reaction.emoji} at {timestamp}")

    # async def on_reaction_remove(self, reaction, user):
    #     if str(user.id) in TUSERS:
    #         timestamp = f"<t:{int(time.time())}:F>"
    #         print(f"Reaction removed by {user.name} to message {reaction.message.content} - {reaction.emoji} at {timestamp}")
    #         channel = client.get_channel(await self.get_channel_for_user(user.id, 'unspoken'))
    #         if channel:
    #             await channel.send(f"Reaction removed by {user.name} to message {reaction.message.content} - {reaction.emoji} at {timestamp}")
    #               
    # detects bot updates but not user games or status changes im retarded i guess               
    # async def on_presence_update(self, before, after):
    #     print(f"detected presence update: {before.status} to {after.status} and {before.activity} to {after.activity}")
    #     if str(after.id) in TUSERS:
    #         timestamp = f"<t:{int(time.time())}:F>"
    #         channel = client.get_channel(await self.get_channel_for_user(after.id, 'news'))
    #         if channel:
    #             if before.status != after.status:   
    #                 await channel.send(f"**Presence updated** for **[**{after.name}**]** from {before.status} to {after.status} at {timestamp}")
    #             if before.activity != after.activity:
    #                 await channel.send(f"**Activity updated** for **[**{after.name}**]** from {before.activity} to {after.activity} at {timestamp}")    
    
# Initialize the Discord client and run it

## TODO:
# 0. add fallback text logging in data direcotry for all events incase we got to nuke the discord server.
# 1. Create a system for tracking HVS (High Value Servers) where (High Value Targets) frequenet with more detailed tracking and logging about the server and its members and changes.
# 2. Create fine tuned tracking system for specific High Value Targets (HVTs) with more detailed tracking and logging, specifically leveraging the friendship relationship to get things like bio, status, and game activity as well as spotify activity & mutal servers.
# 3. Figure out if we can get game presence without friendship relationship and how to log them the best way possible.
# 4. Add support for watching reactions added to messages (using raw events) reacion events 
# 5. Add support for watching voice channels in targeted server where targets frequent, later explore voice support for call recording and monitoring user voice state changes (mute, deafen, etc)
# 6. Can we log when mutal servers change for tracked users like when they leave a mutual guild? (we need at least 3 mutal server to recivie message events from a target user in any server)
# 7. Addition of commands to manage targeted users and their tracking settings, give fine tuned tracking control for all users, (one has all 4 chgannels, one has only 2, one has all 4 but only logs messages and edits, etc)
# 8. Add support for watching user roles and role changes in tracked servers (HVT system)
# 9. Add support for watching user server profile changes like banner and icon in tracked servers (HVS system)
# 10. Mutal server discovery via stickers guild attribute to expand our reach for tracking users.
