import util
import datetime
import pytz
import pytest


timestamp_59_minutes_old = int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - 3540
timestamp_60_minutes_old = int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - 3600
timestamp_61_minutes_old = int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - 3660
timestamp_24_hours_old = int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - 3600 * 24
timestamp_72_hours_old = int(datetime.datetime.now(tz=pytz.UTC).timestamp()) - 3600 * 72
@pytest.mark.parametrize("test_input_initial_timestamp, expected", [(timestamp_59_minutes_old, 0), 
																																		(timestamp_60_minutes_old, 1), 
																																		(timestamp_61_minutes_old, 1),
																																		(timestamp_24_hours_old, 24),
																																		(timestamp_72_hours_old, 72)]
									)
def test_hours_elapsed(test_input_initial_timestamp, expected):
	assert util.calc_hours_elapsed_from_initial_mention(test_input_initial_timestamp) == expected


@pytest.mark.parametrize("test_input_hours_elapsed, expected", [(0, 1000),
																																(1, 2), 
																																(2, 4), 
																																(3, 4),
																																(4, 6),
																																(24, 48),
																																(48, 72)]
									)									
def test_hours_elapsed(test_input_hours_elapsed, expected):
	assert util.calc_next_remind_interval_from_hours_elapsed(test_input_hours_elapsed) == expected
