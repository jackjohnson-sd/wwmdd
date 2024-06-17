import pandas as pd
from data_load import loadNBA_data
from play_by_play import generatePBP
from plots import plot3, quitGame
 

from settings import defaults
 
dfs         = {}    # has everthing that was in db as dict of DateFrame by column name from DB
db_con      = None  # keep this around to get play_by_play when needed

def main():

    _TEAM       = defaults.get('TEAM')      # OKC
    _START_DAY  = defaults.get('START_DAY') # 2023-01-01
    _STOP_DAY   = defaults.get('STOP_DAY')  # 2023-04-20
    DB_FILENAME = defaults.get('SOURCE')

    _dfs, db_con = loadNBA_data(DB_FILENAME)
    # brutal appoach to get data from the first 'cell' in a data frame
    _team_id = _dfs['team'][_dfs['team'].abbreviation == _TEAM].id.iloc[0]

    qs = f'game_date >= "{_START_DAY} 00:00:00" and game_date <= "{_STOP_DAY} 00:00:00" and team_id_home == "{int(_team_id)}"'
    games = _dfs['game'].query(qs)

    for i, game_data in games.iterrows():

        qs = f"select * from play_by_play where game_id == '{game_data.game_id}'"
        play_by_play = pd.read_sql_query(qs, db_con)

        game_data.play_by_play = play_by_play  
        
        our_playerstints_and_boxscore      = generatePBP(game_data, _TEAM)
        opponent_playerstints_and_boxscore = generatePBP(game_data, _TEAM, OPPONENT=True)

        plot3(_TEAM, game_data,
            our_playerstints_and_boxscore,
            opponent_playerstints_and_boxscore)
                # next game or quit
        # prompt for quit (bes) 
        if(quitGame()==True):
            break
    db_con.close()

