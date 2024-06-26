import os
import discord
import asyncio
from discord.ext import commands, tasks
from datetime import datetime
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

TOKEN = os.getenv("TOKEN")
ROOM_CREATOR_CHANNEL_ID = int(os.getenv("ROOM_CREATOR_CHANNEL_ID"))
GUILD = int(os.getenv("GUILD"))
CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID = int(os.getenv("CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID"))
IMAGES = ["night.gif", "morning.gif", "day.gif", "evening.gif"]
list = [] #list of temporary channels

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event   
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    guild = bot.get_guild(GUILD)
    # Read images once after start
    images = await read_images()
    # Start task to change avatar every 6 hours
    change_avatar.start(images,guild)  

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
        with open("img/"+filename, "rb") as image_file:
            image_data = image_file.read()
            images.append(image_data)
    return images


@bot.command()
async def status(ctx):
    embed = discord.Embed(title="Ok", color=discord.Color.green())
    await ctx.reply(embed=embed)


@tasks.loop(minutes=10)
async def change_avatar(images,guild):
    # Get current Ukraine time
    hour = datetime.now(timezone('Europe/Kiev')).hour
    # Check is it time to change avatar
    if hour==0:
    	await guild.edit(icon=images[0])
    elif hour==6:
    	await guild.edit(icon=images[1])
    elif hour==12:
    	await guild.edit(icon=images[2])
    elif hour==18:
    	await guild.edit(icon=images[3])

async def update_total_members(guild):
    # Find channel to update
    total_members_channel = guild.get_channel(CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID)
    # Get the number of members on the server
    number_of_members = len(guild.members)
    # Update the channel name with member count
    await total_members_channel.edit(name=f"⚪️▏Members: {number_of_members}")

bot.run(TOKEN)