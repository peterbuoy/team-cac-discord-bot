import datetime
import pytest
import argparse
import pytz
import discord
import os
import sqlite3
from discord.ext import tasks, commands
from dotenv import load_dotenv
load_dotenv()


parser = argparse.ArgumentParser(description="Set environment flag.")
parser.add_argument("--env", type=str, required=True, help='set to prod or dev')
args = parser.parse_args()
TARGET_USER_ID = 0
TARGET_CHANNEL_ID = 0
if args.env == "dev":
	# Peter, Test
	TARGET_USER_ID = 131965968980246529
	TARGET_CHANNEL_ID = 974545078695653439
elif args.env == "prod":
	# Other guy, Prod
	TARGET_USER_ID = 974545078695653439
	TARGET_CHANNEL_ID = 274417939866714113
else:
	print(f"\033[93mArgument error:\033[0m\n{args.env} is not a valid flag for --env. Please specify dev or prod as an argument for --env.")
	exit()
print(f"{args.env} environment activated.")

conn = sqlite3.connect("cac.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mention (mentioned_user_discord_id TEXT, mention_timestamp INTEGER, mention_message_id TEXT, next_reminder_time_unix INTEGER)")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='%', intents=intents)


@bot.event
async def on_ready():
	print(f'{bot.user.name}: Bot Ready at {datetime.datetime.now()}')
	print('------')


@bot.command()
async def reminders(ctx):
	testing_channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
	rows = cursor.execute("SELECT * from mention").fetchall()
	if len(rows) > 0:
		message = ""
		for row in rows:
			try:
				message += f"<@{row[0]}> was mentioned at <t:{row[1]}:F> in the following message {(await testing_channel.fetch_message(row[2])).jump_url}\n"
			except discord.NotFound:
				message += f"<@{row[0]}> was mentioned at <t:{row[1]}:F> in a message but it has been deleted.\n"
		await ctx.send(message)
	else:
		await ctx.send("The reply queue is empty for now, good job!")


@bot.event
async def on_message(message: discord.Message):
	if message.author == bot.user:
		return
	# This will not count replies as a mention
	if TARGET_USER_ID in map(lambda x: x.id, message.mentions) and message.reference is None:
		unix_timestamp = int(datetime.datetime.now(tz=pytz.UTC).timestamp())
		print('unix_timestamp: ', unix_timestamp)
		# We add 3600 (seconds) to the unix timestamp to set the next_reminder_time_unix column to one hour after a valid mention message
		cursor.execute("INSERT INTO mention VALUES(?, ?, ?, ?)", (TARGET_USER_ID, unix_timestamp, message.id, unix_timestamp + 3600))
		conn.commit()
	# This ensures that only replies to a valid mention have their message content repeated in the channel
	if (message.author.id == TARGET_USER_ID and message.reference is not None and isMessageValidMention(message.reference.message_id)):
		reply_id = str(message.reference.message_id)
		hit = cursor.execute("DELETE FROM mention WHERE mention_message_id = ?", (reply_id, )).fetchone()
		conn.commit()
		if type(hit) == None:
			return
		else:	
			await message.channel.send(f"You have replied to one message with the following response:\n >>> {message.clean_content}")
	await bot.process_commands(message)


def calc_next_remind_interval_from_hours_elapsed(hours_elapsed: int):
	if hours_elapsed >= 24:
		return (hours_elapsed // 24) * 24
	elif hours_elapsed >= 12:
		return 24
	elif hours_elapsed >= 6:
		return 12
	elif hours_elapsed >= 4:
		return 6
	elif hours_elapsed >= 2:
		return 4
	elif hours_elapsed >= 1:
		return 2
	# the 1 hour reminder is already baked into the row upon insertion
	else:
		print("Something has gone terrible wrong in calculating the next reminder time function.")


def isMessageValidMention(message_id: int) -> bool:
	message = cursor.execute("SELECT * FROM mention WHERE mention_message_id = ?", (message_id,)).fetchone()
	if message is None:	
		return False
	else:
		return True


def calc_hours_elapsed_from_initial_mention(mention_unix_timestamp: int) -> int:
	return (int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - mention_unix_timestamp) // 3600


@tasks.loop(seconds=60)
async def remind_mentioned_to_reply():
	target_channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
	reminders = cursor.execute("SELECT * from mention WHERE next_reminder_time_unix < ((julianday('now') - 2440587.5) * 86400.0)").fetchall()

	if len(reminders) < 1:
		return

	reminder_message = f"<@{TARGET_USER_ID}>\nBelow are the message(s) you have not replied to in a timely manner.\nPlease Discord **reply** to the linked message to remove these reminders.\n"
	for reminder in reminders:
		hours_elapsed_since_initial_mention = calc_hours_elapsed_from_initial_mention(reminder[1])
		new_next_reminder_interval = calc_next_remind_interval_from_hours_elapsed(hours_elapsed_since_initial_mention)
		# initial timestamp plus the next interval (calculated from the hours elapsed) will give you the new reminder time
		# this is so that if the bot goes down, it will give the proper remind time
		new_next_reminder_time = int(reminder[1]) + (new_next_reminder_interval * 3600)
		try:
			message_with_mention_jump_url = (await target_channel.fetch_message(reminder[2])).jump_url
			reminder_message += f"{(reminder[3] - reminder[1]) // 3600} hour(s) ago.\n{message_with_mention_jump_url}\n\n"
			cursor.execute("UPDATE mention SET next_reminder_time_unix = ? WHERE mention_message_id = ?", (new_next_reminder_time, reminder[2]))
			conn.commit()
		except discord.NotFound:
			cursor.execute("DELETE FROM mention WHERE mention_message_id = ?", (reminder[2],))
			conn.commit()
	await target_channel.send(reminder_message)
		

# not fault-tolerant at all, must put into load and unload cog that starts and stops
remind_mentioned_to_reply.start()

# discord bot token is in .env file that is not in source control
bot.run(os.environ['DISCORD_BOT_TOKEN'])
 