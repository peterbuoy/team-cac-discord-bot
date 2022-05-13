from datetime import datetime
import discord
import os
from discord.ext import tasks, commands
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='%', intents=intents)
# maybe just use sqlite for easy persistence. don't even bother with intermediate data structures unless necessary
user_mentions_dict = {}

@bot.event
async def on_ready():
	print(f'{bot.user.name}: Bot Ready')
	print('------')	

@bot.event
async def on_message(message: discord.Message):
	if message.author == bot.user:
		return
	# change this to only if david's ID is mentioned
	if len(message.mentions) > 0:
		for user in message.mentions:
			user_mentions_dict[user.mention] = message.created_at

@tasks.loop(seconds=30.0)
async def remind_mentioned_to_reply():
	testing_channel = await bot.fetch_channel("974545078695653439")
	if len(user_mentions_dict) > 0: 
		message = "The following users have been mentioned but have failed to respond in a timely manner: \n"
		for userMention, message_timestamp in user_mentions_dict.items():
			# not ideal since this is naive utc time :/
			utc_time = datetime.utcnow()
			message += f"{userMention} has not responded for {(utc_time - message_timestamp).total_seconds()} seconds"
		await testing_channel.send(message)

# only applies to David
# increasing amount of time for each reminder
# 1, 2, 4, 6, 12, 24, 48, 72, 96, 120, etc in increments of 24
# must reply to specific message that mentioned him
# hyperlink message that he needs to reply to
# 1, 2, 3

# not fault-tolerant at all, must put into load and unload cog that starts and stops
remind_mentioned_to_reply.start()

# discord bot token is in .env file that is not in source control
bot.run(os.environ['DISCORD_BOT_TOKEN'])
 