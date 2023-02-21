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
IMAGES = ["avatar_1.jpg", "avatar_2.jpg", "avatar_3.jpg", "avatar_4.jpg"]
list = [] #list of temporary channels

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
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
                new_channel_name = f'🌴 Chill ({member.name})'
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
        hour = datetime.utcnow().hour
        if hour in (4,10,16,22):
            print("time to change avatar " + str(hour))
            await self.change_avatar(images,hour)
        else:
            print("not this time "+ str(hour))

keep_alive()
if __name__ == '__main__':
    Bot().run(TOKEN)