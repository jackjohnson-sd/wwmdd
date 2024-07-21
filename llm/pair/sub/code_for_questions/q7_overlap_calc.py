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

# Function to calculate playing time within a specific time frame
def calculate_playing_time_within_period(player_name, period, start_time_str, end_time_str):
    # Convert start and end times to game time
    start_time_game = convert_to_game_time(period, start_time_str)
    end_time_game = convert_to_game_time(period, end_time_str)
    
    # Filter player's start and end times within the specific period
    player_starts = play_by_play_df[(play_by_play_df['player2_name'] == player_name) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]
    player_ends = play_by_play_df[(play_by_play_df['player1_name'] == player_name) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]

    player_starts_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player_starts.iterrows()]
    player_ends_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player_ends.iterrows()]

    total_playing_time = 0
    
    for start, end in zip(player_starts_game_time, player_ends_game_time):
        if start < end_time_game and end > start_time_game:
            actual_start = max(start, start_time_game)
            actual_end = min(end, end_time_game)
            total_playing_time += actual_end - actual_start
    
    return total_playing_time

# Calculate playing time for Gilgeous-Alexander in the first 6 minutes of period 1
playing_time_first_6_minutes = calculate_playing_time_within_period('Shai Gilgeous-Alexander', 1, '12:00', '6:00')

# Convert total playing time to minutes and seconds
minutes_played = playing_time_first_6_minutes // 60
seconds_played = playing_time_first_6_minutes % 60

print(f"Shai Gilgeous-Alexander played {minutes_played}:{seconds_played:02d} in the first 6 minutes of period 1.")
