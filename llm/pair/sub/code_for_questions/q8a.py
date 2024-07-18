import pandas as pd

# Function to convert period and pctimestring to game_time
def convert_to_game_time(period, pctimestring):
    minutes, seconds = map(int, pctimestring.split(':'))
    game_time = (period - 1) * 720 + (720 - (minutes * 60 + seconds))
    return game_time

# Function to calculate the overlap between two stints
def calculate_overlap(stint1, stint2):
    start1, end1 = stint1
    start2, end2 = stint2
    start_overlap = max(start1, start2)
    end_overlap = min(end1, end2)
    if start_overlap < end_overlap:
        return end_overlap - start_overlap
    return 0

# Function to get stints for a player
def get_stints(sub_events, player):
    starts = sub_events[sub_events['player2_name'] == player]
    ends = sub_events[sub_events['player1_name'] == player]
    starts['game_time'] = starts.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)
    ends['game_time'] = ends.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)
    stints = [(row['game_time'], ends[ends['game_time'] > row['game_time']]['game_time'].min()) for index, row in starts.iterrows()]
    return [(start, end) for start, end in stints if pd.notna(end)]

# Modified function to calculate overlap time between two players
def player_stint_overlap(data, player1, player2, period=None):
    # Calculate game_time for all events
    data['game_time'] = data.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)

    # Filter substitution events
    sub_events = data[data['eventmsgtype'] == 'SUB']

    # Get stints for each player
    player1_stints = get_stints(sub_events, player1)
    player2_stints = get_stints(sub_events, player2)

    # Filter stints by period if specified
    if period:
        start_period = (period - 1) * 720
        end_period = period * 720
        player1_stints = [(start, min(end, end_period)) for start, end in player1_stints if start >= start_period and start < end_period]
        player2_stints = [(start, min(end, end_period)) for start, end in player2_stints if start >= start_period and start < end_period]

    # Calculate overlaps
    total_overlap = 0
    for p1_stint in player1_stints:
        for p2_stint in player2_stints:
            overlap = calculate_overlap(p1_stint, p2_stint)
            total_overlap += overlap

    return total_overlap

# Load the game data
file_path = 'llm/pair/sub/OKCvGSW20230130.csv'
game_data = pd.read_csv(file_path)

# Example usage
player1 = "Josh Giddey"
player2 = "Kenrich Williams"

# Calculate and print overlaps for each period
for period in range(1, 5):
    overlap_time = player_stint_overlap(game_data, player1, player2, period)
    overlap_minutes, overlap_seconds = divmod(overlap_time, 60)
    print(f"8{chr(96 + period)}. Overlap in period {period}: {overlap_minutes} minutes and {overlap_seconds} seconds")

# Calculate and print total overlap
total_overlap_time = player_stint_overlap(game_data, player1, player2)
total_overlap_minutes, total_overlap_seconds = divmod(total_overlap_time, 60)
print(f"\n8e. Total overlap in the game: {total_overlap_minutes} minutes and {total_overlap_seconds} seconds")
