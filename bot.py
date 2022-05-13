import datetime
import pytz
import discord
import os
import sqlite3
from discord.ext import tasks, commands
from dotenv import load_dotenv
load_dotenv()

conn = sqlite3.connect("cac.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mention (mentioned_discord_id TEXT, mention_timestamp INTEGER, mention_message_id TEXT)")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='%', intents=intents)

TARGETED_USER_ID = 131965968980246529

@bot.command()
async def display(ctx):
	testing_channel = await bot.fetch_channel("974545078695653439")
	rows = cursor.execute("SELECT * from mention").fetchall()
	if len(rows) > 0:
		message = ""
		for row in rows:
			message += f"<@{row[0]}> was mentioned at {row[1]} in the following message {(await testing_channel.fetch_message(row[2])).jump_url}"
		await ctx.send(message)

@bot.event
async def on_ready():
	print(f'{bot.user.name}: Bot Ready')
	print('------')	

@bot.event
async def on_message(message: discord.Message):
	if message.author == bot.user:
		return
	if len(message.mentions) == 1 and message.mentions[0].id == TARGETED_USER_ID:
		utc_aware_timestamp = pytz.utc.localize(datetime.datetime.now())
		assert utc_aware_timestamp.tzinfo != None
		cursor.execute("INSERT INTO mention VALUES(?, ?, ?)", (TARGETED_USER_ID, utc_aware_timestamp, message.id))
		conn.commit()
	await bot.process_commands(message)

@tasks.loop(seconds=30.0)
async def remind_mentioned_to_reply():
	testing_channel = await bot.fetch_channel("974545078695653439")
	# if len(user_mentions_dict) > 0: 
	# 	message = "The following users have been mentioned but have failed to respond in a timely manner: \n"
	# 	for userMention, message_timestamp in user_mentions_dict.items():
	# 		# not ideal since this is naive utc time :/
	# 		utc_time = datetime.utcnow()
	# 		message += f"{userMention} has not responded for {(utc_time - message_timestamp).total_seconds()} seconds"
	# 	await testing_channel.send(message)

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
 