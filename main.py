import os
import discord
import asyncio
from discord.ext import commands, tasks
from webserver import keep_alive
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ROOM_CREATOR_CHANNEL_ID = int(os.getenv("ROOM_ID"))
GUILD = int(os.getenv("GUILD"))
CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID = int(os.getenv("CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID"))
CHANNEL_TO_SHOW_ONLINE_MEMBERS_ID = int(os.getenv("CHANNEL_TO_SHOW_ONLINE_MEMBERS_ID"))
IMAGES = ["avatar_night.gif", "avatar_morning.gif", "avatar_day.gif", "avatar_evening.gif"]
list = [] #list of temporary channels
# Reading from file, if there are not deleted channels
f = open('id_temp.txt')
for id in f:
    list.append(int(id))
f.close()

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(intents=intents,command_prefix='!')


@bot.event   
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    guild = bot.get_guild(GUILD)
    # Read images once after start
    images = await read_images()
    # Start task to change avatar every 6 hours
    change_avatar.start(images,guild)
    # Start task to update online members count every minute
    update_online_members.start(guild)    

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        # User has joined the "Room creator" channel
        if after.channel and after.channel.id == ROOM_CREATOR_CHANNEL_ID:
            # Create a new voice channel with max bitrate
            new_channel_name = f'🔸 Room ({member.name})'
            new_channel = await member.guild.create_voice_channel(new_channel_name, category=after.channel.category, bitrate= member.guild.bitrate_limit,rtc_region="rotterdam")
            # Move the user to the new channel
            await member.move_to(new_channel)
            # Grant the user permission to manage the new channel
            await new_channel.set_permissions(member, manage_channels=True)
            # Add created channel to list to mark it as created by the bot
            list.append(new_channel.id)
        # Check if the old channel is now empty and delete it (if it was created by the bot)
        if before.channel and not before.channel.members and before.channel.id in list:
            # Delete channel from list of temporary channels
            list.remove(before.channel.id)
            # Deleting temporary channel
            await before.channel.delete()
    # Write in file to save if bot closed
    f = open('id_temp.txt', 'w')
    for id in list:
        f.write(str(id) + '\n')
    f.close()

@bot.event
async def on_member_join(member):
    # Update the channels when a member joins or leaves
    await update_total_members(member.guild)

@bot.event
async def on_member_remove(member):
    # Update the channels when a member joins or leaves
    await update_total_members(member.guild)

async def read_images():
    images = []
    for filename in IMAGES:
        with open(filename, "rb") as image_file:
            image_data = image_file.read()
            images.append(image_data)
    return images
   
@tasks.loop(minutes=10)
async def change_avatar(images,guild):
    # Get current UTC time
    hour = datetime.utcnow().hour
    # Check is it time to change avatar
    match hour:
        case 22:
            await guild.edit(icon=images[0])
        case 4:
            await guild.edit(icon=images[1])
        case 10:
            await guild.edit(icon=images[2])
        case 16:
            await guild.edit(icon=images[3])
        case _:
            return
            #print("not this time")

async def update_total_members(guild):
    # Find channel to update
    total_members_channel = guild.get_channel(CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID)
    # Get the number of members on the server
    number_of_members = len(guild.members)
    # Update the channel name with member count
    await total_members_channel.edit(name=f"⚪️▏Members: {number_of_members}")

@tasks.loop(minutes=1)
async def update_online_members(guild):
    # Find the channel to update
    online_members_channel = guild.get_channel(CHANNEL_TO_SHOW_ONLINE_MEMBERS_ID)
    # Get the number of members who are currently online
    number_of_online_members = len([m for m in guild.members if m.status != discord.Status.offline])
    # Update the channel name with online member count
    await online_members_channel.edit(name=f"🟢▏Online: {number_of_online_members}")

keep_alive()
bot.run(TOKEN)