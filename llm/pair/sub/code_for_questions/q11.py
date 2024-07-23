import pandas as pd

# Load the CSV file
file_path = 'llm/pair/sub/OKCvGSW20230130.csv'
df = pd.read_csv(file_path)

# Define a function to convert pctimestring to game time in seconds
def convert_to_game_time(period, pctimestring):
    minutes, seconds = map(int, pctimestring.split(':'))
    return (period - 1) * 720 + (720 - (minutes * 60 + seconds))

# Filter SUB events related to Josh Giddey and Shai Gilgeous-Alexander
giddey_subs = df[(df['eventmsgtype'] == 'SUB') & ((df['player1_name'] == 'Josh Giddey') | (df['player2_name'] == 'Josh Giddey'))]
gilgeous_alexander_subs = df[(df['eventmsgtype'] == 'SUB') & ((df['player1_name'] == 'Shai Gilgeous-Alexander') | (df['player2_name'] == 'Shai Gilgeous-Alexander'))]

# Add game_time column to SUB events
giddey_subs['game_time'] = giddey_subs.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)
gilgeous_alexander_subs['game_time'] = gilgeous_alexander_subs.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)

# Sort by game time
giddey_subs = giddey_subs.sort_values(by='game_time')
gilgeous_alexander_subs = gilgeous_alexander_subs.sort_values(by='game_time')

# Create stints for both players
def create_stints(subs):
    stints = []
    current_stint_start = None
    for _, row in subs.iterrows():
        if pd.isna(row['player1_name']):  # Player starts playing
            current_stint_start = row['game_time']
        else:  # Player stops playing
            if current_stint_start is not None:
                stints.append((current_stint_start, row['game_time']))
                current_stint_start = None
    return pd.DataFrame(stints, columns=['start_time', 'end_time'])

giddey_stints_df = create_stints(giddey_subs)
gilgeous_alexander_stints_df = create_stints(gilgeous_alexander_subs)

# Filter FOUL events committed by Josh Giddey
giddey_fouls = df[(df['eventmsgtype'] == 'FOUL') & (df['player1_name'] == 'Josh Giddey')]

# Add game_time column to fouls
giddey_fouls['game_time'] = giddey_fouls.apply(lambda row: convert_to_game_time(row['period'], row['pctimestring']), axis=1)

# Function to check if a given game time falls within the overlap of two stints
def is_in_overlap(foul_time, stints_giddey, stints_sga):
    for _, giddey_stint in stints_giddey.iterrows():
        for _, sga_stint in stints_sga.iterrows():
            overlap_start = max(giddey_stint['start_time'], sga_stint['start_time'])
            overlap_end = min(giddey_stint['end_time'], sga_stint['end_time'])
            if overlap_start <= foul_time <= overlap_end:
                return True
    return False

# Calculate the number of fouls committed by Giddey while playing with SGA
fouls_while_playing_with_sga = sum(is_in_overlap(foul['game_time'], giddey_stints_df, gilgeous_alexander_stints_df) for _, foul in giddey_fouls.iterrows())

print(fouls_while_playing_with_sga)
