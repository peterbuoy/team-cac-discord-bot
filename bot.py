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

def calc_next_remind_time(hours: int):
	# Reminder times are hardcoded up to 24 hours. After 24 hours, reminder times are every 24 hours.
	# 1, 2, 4, 6, 12, 24, 48, 72, 96, etc
	if hours == 0:
		return 1
	elif hours == 1:
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

def calc_prev_remind_time(hours: int):
	if hours == 1:
		return 0
	elif hours == 2:
		return 1
	elif hours == 4:
		return 2
	elif hours == 6:
		return 4
	elif hours == 12:
		return 6
	elif hours == 24:
		return 12
	elif hours > 24:
		return hours - 24

def define_custom_func():
	conn.create_function('calc_next_remind_time', 1, calc_next_remind_time)
define_custom_func()

TARGETED_USER_ID = 212395768273829890
TARGET_CHANNEL_ID = 274417939866714113

@bot.command()
async def display(ctx):
	testing_channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
	rows = cursor.execute("SELECT * from mention").fetchall()
	if len(rows) > 0:
		message = ""
		for row in rows:
			message += f"<@{row[0]}> was mentioned at <t:{row[1]}:F> in the following message {(await testing_channel.fetch_message(row[2])).jump_url}\n"
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
	if len(message.mentions) > 0 and TARGETED_USER_ID in map(lambda x: x.id, message.mentions):
		unix_timestamp = int(datetime.datetime.now(tz=pytz.UTC).timestamp())
		cursor.execute("INSERT INTO mention VALUES(?, ?, ?, ?)", (TARGETED_USER_ID, unix_timestamp, message.id, 1))
		conn.commit()
	# pinning a message will count as replying to a message
	if (message.author.id == TARGETED_USER_ID and message.reference != None):
		reply_id = str(message.reference.message_id)
		hit = cursor.execute("DELETE FROM mention WHERE mention_message_id = ?", (reply_id, )).fetchone()
		conn.commit()
		if type(hit) == None:
			return
		else:
			await message.channel.send(f"You have replied to one message with the following response:\n >>> {message}")
	await bot.process_commands(message)

@tasks.loop(seconds=60)
async def remind_mentioned_to_reply():
	testing_channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
	reminders = cursor.execute("UPDATE mention SET remind_time_in_hours = calc_next_remind_time(remind_time_in_hours) WHERE (remind_time_in_hours * 60 * 60) < (((julianday('now') - 2440587.5) * 86400.0) - mention_timestamp) RETURNING *").fetchall()
	conn.commit()
	if len(reminders) < 1:
		return
	# mentioned_user_discord_id TEXT, mention_timestamp INTEGER, mention_message_id TEXT, remind_time_in_hours INTEGER
	# this only mentions the first person in the list... which is only one person anyway LOL
	reminder_message = f"<@{TARGETED_USER_ID}>\nBelow are the message(s) you have not replied to in a timely manner.\nPlease Discord **reply** to the linked message to remove these reminders.\n"
	for reminder in reminders:
		try:
			message_with_mention_jump_url = (await testing_channel.fetch_message(reminder[2])).jump_url
		except discord.NotFound:
			# uncomment the DELETE statement when you want to fix the bot lmao
		  # cursor.execute("DELETE FROM mention WHERE message_mention_id = ?", reminder[2])
			await testing_channel.send(reminder_message)
		reminder_message += f"{calc_prev_remind_time(reminder[3])} hour(s) ago.\n{message_with_mention_jump_url}\n\n"
	if reminder_message != "":
		await testing_channel.send(reminder_message)

# not fault-tolerant at all, must put into load and unload cog that starts and stops
remind_mentioned_to_reply.start()

# discord bot token is in .env file that is not in source control
bot.run(os.environ['DISCORD_BOT_TOKEN'])
 