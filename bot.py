from cgi import test
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
cursor.execute("CREATE TABLE IF NOT EXISTS mention (mentioned_user_discord_id TEXT, mention_timestamp INTEGER, mention_message_id TEXT, remind_time_in_hours INTEGER)")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='%', intents=intents)

def define_custom_func():
	conn.create_function('calc_next_remind_time', 1, calc_next_remind_time)

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
	else:
		await ctx.send("The reply queue is empty for now, good job!")

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
		cursor.execute("INSERT INTO mention VALUES(?, ?, ?, ?)", (TARGETED_USER_ID, utc_aware_timestamp, message.id, 1))
		conn.commit()
	if (message.author.id == TARGETED_USER_ID and message.reference != None):
		reply_id = str(message.reference.message_id)
		hit = cursor.execute("DELETE FROM mention WHERE mention_message_id = ?", (reply_id, )).fetchone()
		conn.commit()
		if type(hit) == None:
			return
		else:
			await message.channel.send("You have replied to one message. Your response has been recorded.")
	await bot.process_commands(message)

@tasks.loop(seconds=10)
async def remind_mentioned_to_reply():
	testing_channel = await bot.fetch_channel("974545078695653439")
	# rough sketch
	reminders = cursor.execute("UPDATE mention SET remind_time_in_hours = calc_next_remind_time(remind_time_in_hours) WHERE remind_time_in_hours < unixepoch() - mention_timestamp RETURNING").fetchall()
	await testing_channel.send(reminders)
	# if len(user_mentions_dict) > 0: 
	# 	message = "The following users have been mentioned but have failed to respond in a timely manner: \n"
	# 	for userMention, message_timestamp in user_mentions_dict.items():
	# 		# not ideal since this is naive utc time :/
	# 		utc_time = datetime.utcnow()
	# 		message += f"{userMention} has not responded for {(utc_time - message_timestamp).total_seconds()} seconds"
	# 	await testing_channel.send(message)

# not fault-tolerant at all, must put into load and unload cog that starts and stops
remind_mentioned_to_reply.start()
define_custom_func()

def calc_next_remind_time(hours: int):
	# Reminder times are hardcoded up to 24 hours. After 24 hours, reminder times are every 24 hours.
	# 1, 2, 4, 6, 12, 24, 48, 72, 96, etc
	if hours == 1:
		return 2
	elif hours == 2:
		return 4
	elif hours == 4:
		return 6
	elif hours == 6:
		return 12
	elif hours == 12:
		return 24
	elif hours >= 24:
		return hours + 24

# discord bot token is in .env file that is not in source control
bot.run(os.environ['DISCORD_BOT_TOKEN'])
 