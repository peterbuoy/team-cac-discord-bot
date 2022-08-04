import datetime
import pytz
import sqlite3


def calc_hours_elapsed_from_initial_mention(mention_unix_timestamp: int) -> int:
	return (int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - mention_unix_timestamp) // 3600


def calc_next_remind_interval_from_hours_elapsed(hours_elapsed: int) -> int:
	if hours_elapsed >= 24:
		return ((hours_elapsed // 24) + 1) * 24
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
		FALLBACK_HOUR_VALUE = 1000
		print(f"Something has gone terribly wrong in the calculation for the next reminder interval. Interval has been set to {FALLBACK_HOUR_VALUE} hours")
		return FALLBACK_HOUR_VALUE


def isMessageValidMention(message_id: int, cursor: sqlite3.Cursor) -> bool:
	message = cursor.execute("SELECT * FROM mention WHERE mention_message_id = ?", (message_id,)).fetchone()
	if message is None:	
		return False
	else:
		return True