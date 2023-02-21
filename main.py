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
IMAGES = ["avatar_night.jpg", "avatar_morning.jpg", "avatar_day.jpg", "avatar_evening.jpg"]
list = [] #list of temporary channels

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix='!', intents=intents)
      
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.guild = self.get_guild(GUILD)
        # Read images once after start
        images = await self.read_images()
        # Start task to change avatar every 6 hours
        self.change_avatar_task.start(images)

    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            # User has joined the "Room creator" channel
            if after.channel and after.channel.id == ROOM_CREATOR_CHANNEL_ID:
                # Create a new voice channel with max bitrate
                new_channel_name = f'🔸 Room ({member.name})'
                new_channel = await member.guild.create_voice_channel(new_channel_name, category=after.channel.category, bitrate=96000,reason = "Bot Created")
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

    async def change_avatar(self,images,hour):
        # Define index of image by hour
        match hour:
            case 22:
                image_index = 0
            case 4:
                image_index = 1
            case 10:
                image_index = 2
            case 16:
                image_index = 3

        # Get image for new avatar
        await self.guild.edit(icon=images[image_index])
    
    async def read_images(self):
        images = []
        for filename in IMAGES:
            with open(filename, "rb") as image_file:
                image_data = image_file.read()
                images.append(image_data)
        return images
    
    @tasks.loop(minutes=10)
    async def change_avatar_task(self,images):
        # Get current UTC time
        hour = datetime.utcnow().hour
        # Check is it time to change avatar
        if hour in (4,10,16,22):
            await self.change_avatar(images,hour)

    async def on_member_join(self,member):
        # Update the channel name when a member joins
        await self.update_channel_names(member.guild)
    
    async def on_member_remove(self,member):
        # Update the channel name when a member leaves
        await self.update_channel_names(member.guild)

    async def on_presence_update(self,member,_):
        # Update the channels when a member's presence changes
        await self.update_channel_names(member.guild)
    
    async def update_channel_names(self,guild):
        # Find the channel to update
        total_members_channel = guild.get_channel(CHANNEL_TO_SHOW_TOTAL_MEMBERS_ID)
        online_members_channel = guild.get_channel(CHANNEL_TO_SHOW_ONLINE_MEMBERS_ID)
        # Get the number of members on the server
        number_of_members = len(guild.members)
        # Get the number of members who are currently online
        number_of_online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        # Update the channel names with the member count
        await total_members_channel.edit(name=f"Members: {number_of_members}")
        await online_members_channel.edit(name=f"Online: {number_of_online_members}")


keep_alive()
if __name__ == '__main__':
    Bot().run(TOKEN)