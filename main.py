import sys
import pandas as pd
from data_load import loadNBA_data
from play_by_play import generatePBP
from plots import plot3, settings
import main_web
import main_csv
#
# get arguments, if any
#

def getArgs():

    opponent = None

    for i in range (len(sys.argv)):  # Check for argumentsif sys.argv[i] == '?':
        print("Usage: python argparse3.py <opponent=opponentName> <plotnumber=plotnumber>")

        if (sys.argv[i].find("opponent=")>-1):
            opponent = sys.argv[i].split('=')
            opponent = opponent[1]
            # test print("opponent = ",opponent)

        plotNbrStr = ''
        if (sys.argv[i].find("plotnumber=")>-1):
            plotNbrStr = sys.argv[i].split('=')
        # test print("plotnumber = ",plotNbr)
    
    return opponent

dfs         = {}    # has everthing that was in db as dict of DateFrame by column name from DB
db_con      = None  # keep this around to get play_by_play when needed

def main():

    _TEAM       = settings.get('TEAM')      # OKC
    _START_DAY  = settings.get('START_DAY') # 2023-01-01
    _STOP_DAY   = settings.get('STOP_DAY')  # 2023-04-20
    DB_FILENAME = settings.get('SOURCE')

    _dfs, db_con = loadNBA_data(DB_FILENAME)
    # brutal appoach to get data from the first 'cell' in a data frame
    _team_id = _dfs['team'][_dfs['team'].abbreviation == _TEAM].id.iloc[0]

    qs = f'game_date >= "{_START_DAY} 00:00:00" and game_date <= "{_STOP_DAY} 00:00:00" and team_id_home == "{int(_team_id)}"'
    games = _dfs['game'].query(qs)

    for i, game_data in games.iterrows():

        qs = f"select * from play_by_play where game_id == '{game_data.game_id}'"
        play_by_play = pd.read_sql_query(qs, db_con)

        game_data.play_by_play = play_by_play  # returns a series?
        
        our_playerstints_and_boxscore      = generatePBP(game_data, _TEAM)
        opponent_playerstints_and_boxscore = generatePBP(game_data, _TEAM, OPPONENT=True)

        plot3(_TEAM, game_data,
            our_playerstints_and_boxscore,
            opponent_playerstints_and_boxscore)

    db_con.close()


if __name__ == "__main__":
    import claude
    
    data_source = settings.get('SOURCE')

    if   'WEB:'  in data_source:  main_web.main()
    elif 'FILE:' in data_source:  main_csv.main(data_source.split(':')[1])
    elif 'CLAUDE:' in data_source:  claude.main(data_source.split(':')[1])
    else:                         main()