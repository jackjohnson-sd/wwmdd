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

# Function to calculate the overlap of playing time between two players in a specific period
def calculate_overlap(player1, player2, period):
    # Filter events for both players in the specific period
    player1_starts = play_by_play_df[(play_by_play_df['player2_name'] == player1) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]
    player1_ends = play_by_play_df[(play_by_play_df['player1_name'] == player1) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]
    
    player2_starts = play_by_play_df[(play_by_play_df['player2_name'] == player2) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]
    player2_ends = play_by_play_df[(play_by_play_df['player1_name'] == player2) & (play_by_play_df['period'] == period) & (play_by_play_df['eventmsgtype'] == 'SUB')]

    player1_starts_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player1_starts.iterrows()]
    player1_ends_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player1_ends.iterrows()]

    player2_starts_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player2_starts.iterrows()]
    player2_ends_game_time = [convert_to_game_time(row['period'], row['pctimestring']) for _, row in player2_ends.iterrows()]

    total_overlap_time = 0
    
    for p1_start, p1_end in zip(player1_starts_game_time, player1_ends_game_time):
        for p2_start, p2_end in zip(player2_starts_game_time, player2_ends_game_time):
            overlap_start = max(p1_start, p2_start)
            overlap_end = min(p1_end, p2_end)
            if overlap_start < overlap_end:
                total_overlap_time += overlap_end - overlap_start
    
    return total_overlap_time

# Calculate overlap for each period
overlap_period_1 = calculate_overlap('Josh Giddey', 'Shai Gilgeous-Alexander', 1)
overlap_period_2 = calculate_overlap('Josh Giddey', 'Shai Gilgeous-Alexander', 2)
overlap_period_3 = calculate_overlap('Josh Giddey', 'Shai Gilgeous-Alexander', 3)
overlap_period_4 = calculate_overlap('Josh Giddey', 'Shai Gilgeous-Alexander', 4)

# Convert total overlap time to minutes and seconds for each period
def convert_to_minutes_seconds(overlap_time):
    minutes = overlap_time // 60
    seconds = overlap_time % 60
    return f"{minutes}:{seconds:02d}"

overlap_period_1_ms = convert_to_minutes_seconds(overlap_period_1)
overlap_period_2_ms = convert_to_minutes_seconds(overlap_period_2)
overlap_period_3_ms = convert_to_minutes_seconds(overlap_period_3)
overlap_period_4_ms = convert_to_minutes_seconds(overlap_period_4)

# Calculate total overlap time for the entire game
total_overlap = overlap_period_1 + overlap_period_2 + overlap_period_3 + overlap_period_4
total_overlap_ms = convert_to_minutes_seconds(total_overlap)

print("8a. Overlap in period 1:", overlap_period_1_ms)
print("8b. Overlap in period 2:", overlap_period_2_ms)
print("8c. Overlap in period 3:", overlap_period_3_ms)
print("8d. Overlap in period 4:", overlap_period_4_ms)
print("8e. Total overlap:", total_overlap_ms)
