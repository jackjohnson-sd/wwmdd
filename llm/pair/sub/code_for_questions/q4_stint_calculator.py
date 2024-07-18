import pandas as pd

# Load the CSV file
file_path = 'llm/pair/sub/OKCvGSW20230130.csv'  # Update with your file path
play_by_play_df = pd.read_csv(file_path)

# Function to convert period and pctimestring to game_time in seconds
def convert_to_game_time(period, pctimestring):
    minutes, seconds = map(int, pctimestring.split(':'))
    period_start_time = (period - 1) * 720
    time_remaining_in_period = minutes * 60 + seconds
    game_time = period_start_time + (720 - time_remaining_in_period)
    return game_time

# Filtering events related to Kenrich Williams
williams_starts = play_by_play_df[(play_by_play_df['player2_name'] == 'Kenrich Williams') & (play_by_play_df['eventmsgtype'] == 'SUB')]
williams_ends = play_by_play_df[(play_by_play_df['player1_name'] == 'Kenrich Williams') & (play_by_play_df['eventmsgtype'] == 'SUB')]

# Counting the number of times Kenrich Williams started playing
williams_starts_count = williams_starts.shape[0]

# Extracting the times when Kenrich Williams started playing
williams_start_times = williams_starts[['period', 'pctimestring']].values.tolist()

# Extracting the times when Kenrich Williams ended playing
williams_end_times = williams_ends[['period', 'pctimestring']].values.tolist()

# Calculating game_time for Williams's start and end times
williams_starts_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in williams_starts.iterrows()]
williams_ends_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in williams_ends.iterrows()]

# Calculating stints duration
williams_stints_duration = []
for start_time, end_time in zip(williams_starts_game_time, williams_ends_game_time):
    duration = end_time - start_time
    minutes = duration // 60
    seconds = duration % 60
    williams_stints_duration.append(f"{minutes}:{seconds:02d}")

# Calculating total playing time
total_williams_playing_time = sum([end - start for start, end in zip(williams_starts_game_time, williams_ends_game_time)])
total_williams_minutes = total_williams_playing_time // 60
total_williams_seconds = total_williams_playing_time % 60

# Combining start and end times with stints duration
williams_play_times = [(f"Period {start[0]}, {start[1]} - Period {end[0]}, {end[1]}", duration) 
                       for start, end, duration in zip(williams_start_times, williams_end_times, williams_stints_duration)]

print("4a. Number of times Kenrich Williams started playing:", williams_starts_count)
print("4b. Times Kenrich Williams started playing:", williams_start_times)
print("4c. Times Kenrich Williams ended playing:", williams_end_times)
print("4d. Duration of Williams's stints:", williams_stints_duration)
print("4e. Total minutes Williams played in the game:", f"{total_williams_minutes}:{total_williams_seconds:02d}")
print("4f. Times and durations Williams played:", williams_play_times)
