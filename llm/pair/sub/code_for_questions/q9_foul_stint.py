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

# Function to get foul count for a player's specific stint
def get_foul_count(player_name, stint_number):
    # Filtering events related to the player
    player_starts = play_by_play_df[(play_by_play_df['player2_name'] == player_name) & (play_by_play_df['eventmsgtype'] == 'SUB')]
    player_ends = play_by_play_df[(play_by_play_df['player1_name'] == player_name) & (play_by_play_df['eventmsgtype'] == 'SUB')]

    # Check if the stint number is valid
    if stint_number > len(player_starts) or stint_number > len(player_ends):
        return f"Invalid stint number. {player_name} does not have that many stints."

    # Get the specified stint's start and end
    player_start = player_starts.iloc[stint_number - 1]
    player_end = player_ends.iloc[stint_number - 1]

    # Convert start and end times to game_time in seconds
    player_start_time = convert_to_game_time(player_start['period'], player_start['pctimestring'])
    player_end_time = convert_to_game_time(player_end['period'], player_end['pctimestring'])

    # Filter fouls committed by the player during the specified stint
    fouls_committed = play_by_play_df[(play_by_play_df['player1_name'] == player_name) & 
                                      (play_by_play_df['eventmsgtype'] == 'FOUL')]

    fouls_committed_during_stint = fouls_committed.apply(lambda row: player_start_time <= convert_to_game_time(row['period'], row['pctimestring']) <= player_end_time, axis=1)

    # Count the fouls committed during the specified stint
    fouls_count = fouls_committed_during_stint.sum()

    return fouls_count

# Example usage
player_name = 'Josh Giddey'
stint_number = 5

fouls_count = get_foul_count(player_name, stint_number)
print(f"{player_name} committed {fouls_count} fouls during his {stint_number} stint.")
